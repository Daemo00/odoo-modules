#  Copyright 2020 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import itertools
import random
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import logging, safe_eval

_logger = logging.getLogger(__name__)


class EventTournament(models.Model):
    _name = "event.tournament"
    _description = "Tournament"
    _rec_name = "name"

    name = fields.Char(required=True)
    event_id = fields.Many2one(comodel_name="event.event", string="Event")
    court_ids = fields.Many2many(
        comodel_name="event.tournament.court",
        string="Courts",
        help="Courts available for this tournament",
    )
    match_ids = fields.One2many(
        comodel_name="event.tournament.match",
        inverse_name="tournament_id",
        string="Matches",
    )
    match_count_estimated = fields.Integer(
        string="Estimated match count", compute="_compute_match_count_estimated"
    )
    match_count = fields.Integer(string="Match count", compute="_compute_match_count")
    team_ids = fields.One2many(
        comodel_name="event.tournament.team",
        inverse_name="tournament_id",
        string="Teams",
    )
    component_ids = fields.Many2many(
        comodel_name="event.registration",
        compute="_compute_components",
        string="Components",
    )
    team_count = fields.Integer(string="Team count", compute="_compute_team_count")
    state = fields.Selection(
        selection=[("draft", "Draft"), ("started", "Started"), ("done", "Done")],
        default="draft",
    )
    min_components = fields.Integer(
        string="Minimum components", help="Minimum number of components for a team"
    )
    max_components = fields.Integer(
        string="Maximum components", help="Maximum number of components for a team"
    )
    min_components_female = fields.Integer(
        string="Minimum female components",
        help="Minimum number of female components for a team",
    )
    min_components_male = fields.Integer(
        string="Minimum male components",
        help="Minimum number of male components for a team",
    )
    points_per_win = fields.Integer(
        string="Points per win", help="Points gained for each match won"
    )
    match_mode_id = fields.Many2one(
        string="Match mode", comodel_name="event.tournament.match.mode"
    )
    start_datetime = fields.Datetime(string="Tournament start")
    match_duration = fields.Float(string="Match duration", default=1)
    match_warm_up_duration = fields.Float(strin="Match warm-up duration")
    match_teams_nbr = fields.Integer(
        string="Teams per match", help="Number of teams per match", default=2
    )
    randomize_matches_generation = fields.Boolean(
        string="Randomize", help="Randomize matches generation"
    )
    reset_matches_before_generation = fields.Boolean(
        string="Reset", help="Delete not done matches before generation", default=True
    )
    parent_id = fields.Many2one(
        comodel_name="event.tournament", string="Parent tournament"
    )
    child_ids = fields.One2many(
        comodel_name="event.tournament",
        inverse_name="parent_id",
        string="Sub tournaments",
    )
    notes = fields.Text(string="Notes")

    @api.onchange("event_id")
    def onchange_event_id(self):
        if self.event_id:
            self.start_datetime = self.event_id.date_begin
            self.court_ids = self.event_id.court_ids

    @api.depends("match_ids")
    def _compute_match_count(self):
        for tournament in self:
            tournament.match_count = len(tournament.match_ids)

    @api.depends("team_ids", "match_teams_nbr")
    def _compute_match_count_estimated(self):
        for tournament in self:
            tournament.match_count_estimated = len(
                list(
                    itertools.combinations(
                        tournament.team_ids, tournament.match_teams_nbr
                    )
                )
            )

    @api.depends("team_ids")
    def _compute_team_count(self):
        for tournament in self:
            tournament.team_count = len(tournament.team_ids)

    @api.depends("team_ids.component_ids")
    def _compute_components(self):
        for tournament in self:
            tournament.component_ids = tournament.team_ids.mapped("component_ids")

    def action_draft(self):
        for tournament in self:
            tournament.state = "draft"

    def action_start(self):
        for tournament in self:
            tournament.state = "started"

    def action_done(self):
        for tournament in self:
            tournament.state = "done"

    def action_check_rules(self):
        self.ensure_one()
        self.team_ids.constrain_components_tournament()

    def generate_matches(self):
        """
        Generate matches for the current tournament.
        Matches are generated using `itertools.combinations` built-in
        and they are assigned a time slot in the following fashion:

            1. Tournament start
            2. Court
        """
        self.ensure_one()

        match_duration = self.get_match_duration()
        max_start, min_start = self.get_max_min_start(match_duration)
        courts = self.get_courts()

        matches_teams = self.get_match_tuples()
        if self.randomize_matches_generation:
            random.shuffle(matches_teams)
        if self.reset_matches_before_generation:
            matches_teams = self.reset_matches(matches_teams)

        match_model = self.env["event.tournament.match"]
        matches = match_model.browse()
        while matches_teams:
            match_teams = matches_teams.pop()
            match = match_model.browse()
            curr_start = min_start
            # Try to schedule the match as soon as possible
            while curr_start <= max_start:
                # Try to put this match in a court at curr_start
                for court in courts:
                    try:
                        with self.env.cr.savepoint():
                            # The first match of the court does not need warm-up
                            match = match_model.create(
                                {
                                    "tournament_id": self.id,
                                    "court_id": court.id,
                                    "team_ids": [t.id for t in match_teams],
                                    "time_scheduled_start": curr_start,
                                    "time_scheduled_end": curr_start + match_duration,
                                }
                            )
                    except ValidationError as ve:
                        # The match is not valid, try the following court
                        _logger.info(ve)
                        continue
                    else:
                        # The match is valid
                        matches |= match
                        break
                else:
                    # The match could not be scheduled in any court,
                    # try another time
                    pass

                if match:
                    break
                else:
                    curr_start = curr_start + match_duration
            if not match:
                raise UserError(
                    _("Scheduling impossibru for a match between ")
                    + ", ".join(team.display_name for team in match_teams)
                )
            max_start = max(max_start, match.time_scheduled_end)
            # Try to not make components play two matches in a row:
            # rearrange matches_teams so that components
            # in the latest match are the first ones
            # (popped as late as possible)

            def common_components(m):
                c = self.env["event.registration"].browse()
                for t in m:
                    c |= t.component_ids
                return not (c & match.component_ids)

            matches_teams.sort(key=common_components)

        return matches

    def get_courts(self):
        courts = self.court_ids
        if not courts:
            raise UserError(
                _(
                    "Tournament {tourn_name}:\n"
                    "At least one court is required "
                    "for matches generation."
                ).format(tourn_name=self.display_name)
            )
        return courts

    def get_match_tuples(self):
        if self.match_teams_nbr < 1:
            raise UserError(
                _(
                    "Tournament {tourn_name}:\n"
                    "At least 1 team per match is required "
                    "for matches generation."
                ).format(tourn_name=self.display_name)
            )
        matches_teams = list(
            itertools.combinations(self.team_ids, self.match_teams_nbr)
        )
        return matches_teams

    def get_max_min_start(self, match_duration):
        if not self.start_datetime:
            raise UserError(
                _(
                    "Tournament {tourn_name}:\n"
                    "Start time is required for matches generation."
                ).format(tourn_name=self.display_name)
            )
        warm_up_start = self.start_datetime - timedelta(
            hours=self.match_warm_up_duration
        )
        min_start = warm_up_start
        max_start = max(
            (
                warm_up_start,
                *self.mapped("event_id.tournament_ids." "match_ids.time_scheduled_end"),
            )
        )
        max_start = max_start + match_duration
        return max_start, min_start

    def get_match_duration(self):
        if self.match_duration <= 0:
            raise UserError(
                _("Tournament {tourn_name}:\nA match should have a duration.").format(
                    tourn_name=self.display_name
                )
            )
        match_duration = timedelta(hours=self.match_warm_up_duration) + timedelta(
            hours=self.match_duration
        )
        return match_duration

    def reset_matches(self, matches_teams):
        clean_matches_teams = list()
        done_matches = self.match_ids.filtered(lambda m: m.state == "done")
        for match_teams in matches_teams:
            for done_match in done_matches:
                if done_match.team_ids.ids == [mt.id for mt in match_teams]:
                    # Corresponding match_team found
                    break
            else:
                # Corresponding match_team not found
                clean_matches_teams.append(match_teams)
        matches_teams = clean_matches_teams
        (self.match_ids - done_matches).unlink()
        return matches_teams

    def recompute_matches_points(self):
        self.mapped("team_ids").compute_matches_points()

    def generate_view_matches(self):
        self.generate_matches()
        return self.action_view_matches()

    def set_tournament_domain(self, action):
        """
        Set current tournament domain in `action`.
        """
        self.ensure_one()
        domain = action.get("domain", list())
        domain = safe_eval(domain)
        domain.append(("tournament_id", "=", self.id))
        action.update(domain=domain)

    def set_tournament_context(self, action):
        """
        Set current tournament as default in `action`'s context.
        """
        self.ensure_one()
        context = action.get("context", dict())
        context = safe_eval(context)
        context.update({"default_tournament_id": self.id})
        action.update(context=context)

    def action_view_matches(self):
        self.ensure_one()
        action = self.env.ref("event_tournament.event_tournament_match_action").read()[
            0
        ]
        self.set_tournament_domain(action)
        self.set_tournament_context(action)
        return action

    def action_view_teams(self):
        self.ensure_one()
        action = self.env.ref("event_tournament.event_tournament_team_action").read()[0]
        self.set_tournament_domain(action)
        self.set_tournament_context(action)
        return action

    def open_form_current(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": self._name,
            "res_id": self.id,
            "target": "current",
        }
