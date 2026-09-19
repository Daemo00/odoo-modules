# Copyright 2020 Simone Rubino <daemo00@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models
from odoo.fields import Command, first
from odoo.osv import expression


class EventTournamentMatch(models.Model):
    _name = "event.tournament.match"
    _description = "Tournament match"
    _order = "time_scheduled_start"

    event_id = fields.Many2one(
        related="tournament_id.event_id",
    )

    tournament_id = fields.Many2one(
        comodel_name="event.tournament",
        string="Tournament",
        required=True,
    )
    match_mode_id = fields.Many2one(
        related="tournament_id.match_mode_id",
    )
    court_id = fields.Many2one(
        comodel_name="event.tournament.court",
        string="Court",
        required=True,
        domain="[('event_id', '=', event_id)]",
    )
    set_ids = fields.One2many(
        comodel_name="event.tournament.match.set",
        inverse_name="match_id",
        compute="_compute_set_ids",
        store=True,
        readonly=False,
        string="Sets",
        domain="[('match_id', '=', id)]",
    )
    result_ids = fields.One2many(
        comodel_name="event.tournament.match.set.result",
        inverse_name="match_id",
    )

    team_ids = fields.Many2many(
        comodel_name="event.tournament.team",
        relation="event_tournament_match_team_rel",
        column1="event_tournament_match_id",
        column2="event_tournament_team_id",
        domain="[('tournament_id', '=', tournament_id)]",
    )
    component_ids = fields.Many2many(
        comodel_name="event.registration",
        compute="_compute_components",
        store=True,
    )
    winner_team_id = fields.Many2one(
        comodel_name="event.tournament.team",
        string="Winner",
        compute="_compute_winner_team_id",
        store=True,
        help="Only computed on done matches.",
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done")], default="draft"
    )
    time_scheduled_start = fields.Datetime(
        string="Scheduled start",
    )
    time_scheduled_end = fields.Datetime(
        string="Scheduled end",
    )
    time_done = fields.Datetime()
    stats_ids = fields.One2many(
        comodel_name="event.tournament.match.team_stats",
        inverse_name="match_id",
        readonly=True,
    )

    @api.depends("team_ids.component_ids")
    def _compute_components(self):
        for match in self:
            match.component_ids = match.team_ids.component_ids

    @api.constrains("time_scheduled_start", "time_scheduled_end")
    def _check_tournament_time(self):
        for match in self:
            tournament_start = match.tournament_id.start_datetime
            if (
                tournament_start
                and match.time_scheduled_start
                and tournament_start > match.time_scheduled_start
            ):
                raise exceptions.ValidationError(
                    match.env._(
                        "Match %(match_name)s not valid:\n"
                        "Tournament starts at %(tournament_start)s but "
                        "match starts at %(match_start)s.",
                        match_name=match.display_name,
                        tournament_start=tournament_start,
                        match_start=match.time_scheduled_start,
                    )
                )
            tournament_end = match.tournament_id.end_datetime
            if (
                tournament_end
                and match.time_scheduled_end
                and match.time_scheduled_end > tournament_end
            ):
                raise exceptions.ValidationError(
                    match.env._(
                        "Match %(match_name)s not valid:\n"
                        "Tournament ends at %(tournament_end)s but "
                        "match ends at %(match_end)s.",
                        match_name=match.display_name,
                        tournament_end=tournament_end,
                        match_end=match.time_scheduled_end,
                    )
                )

    @api.constrains("time_scheduled_start", "time_scheduled_end", "component_ids")
    def _check_contemporary(self):
        for match in self:
            contemporary_matches_domain = match.contemporary_match_domain()
            contemporary_matches = self.search(contemporary_matches_domain)
            contemporary_matches = contemporary_matches - match
            match_components = match.component_ids
            for cont_match in contemporary_matches:
                cont_match_components = cont_match.component_ids
                for cont_match_component in cont_match_components:
                    if cont_match_component in match_components:
                        raise exceptions.ValidationError(
                            match.env._(
                                "Match %(match_name)s not valid:\n"
                                "Component %(comp_name)s is already playing "
                                "in match %(cont_match_name)s.",
                                match_name=match.display_name,
                                comp_name=cont_match_component.display_name,
                                cont_match_name=cont_match.display_name,
                            )
                        )

    def contemporary_match_domain(self):
        self.ensure_one()
        domain = []
        if self.time_scheduled_start:
            domain = expression.AND(
                [
                    domain,
                    [
                        "|",
                        ("time_scheduled_start", ">=", self.time_scheduled_start),
                        ("time_scheduled_end", ">", self.time_scheduled_start),
                    ],
                ]
            )
        if self.time_scheduled_end:
            domain = expression.AND(
                [
                    domain,
                    [
                        "|",
                        ("time_scheduled_start", "<", self.time_scheduled_end),
                        ("time_scheduled_end", "<=", self.time_scheduled_end),
                    ],
                ]
            )
        return domain

    @api.constrains("tournament_id", "court_id")
    def _check_court(self):
        for match in self:
            if match.court_id not in match.tournament_id.court_ids:
                raise exceptions.ValidationError(
                    match.env._(
                        "Match %(match_name)s not valid:\n"
                        "Court %(court_name)s is not available for "
                        "tournament %(tourn_name)s.",
                        match_name=match.display_name,
                        court_name=match.court_id.display_name,
                        tourn_name=match.tournament_id.display_name,
                    )
                )

    @api.constrains("court_id", "time_scheduled_start", "time_scheduled_end")
    def _check_court_time(self):
        for match in self:
            court = match.court_id
            overlapping_matches_domain = match.contemporary_match_domain()
            court_domain = [("court_id", "=", court.id)]
            overlapping_matches_domain.extend(court_domain)
            overlapping_matches = self.search(overlapping_matches_domain)
            overlapping_matches = overlapping_matches - match
            if overlapping_matches:
                overlapping_match = first(overlapping_matches)
                raise exceptions.ValidationError(
                    match.env._(
                        "Court %(court_name)s not valid:\n"
                        "match %(match_name)s is overlapping "
                        "%(overlapping_match_name)s.",
                        court_name=court.display_name,
                        match_name=match.display_name,
                        overlapping_match_name=overlapping_match.display_name,
                    )
                )
            if (
                court.time_availability_start
                and match.time_scheduled_start
                and court.time_availability_start > match.time_scheduled_start
            ):
                raise exceptions.ValidationError(
                    match.env._(
                        "Match %(match_name)s not valid:\n"
                        "court %(court_name)s is available "
                        "from %(court_start)s but "
                        "match starts at %(match_start)s.",
                        match_name=match.display_name,
                        court_name=court.display_name,
                        court_start=court.time_availability_start,
                        match_start=match.time_scheduled_start,
                    )
                )
            if (
                court.time_availability_end
                and match.time_scheduled_end
                and court.time_availability_end < match.time_scheduled_end
            ):
                raise exceptions.ValidationError(
                    match.env._(
                        "Match %(match_name)s not valid:\n"
                        "court %(court_name)s is available "
                        "until %(court_end)s but "
                        "match ends at %(match_end)s.",
                        match_name=match.display_name,
                        court_name=court.display_name,
                        court_end=court.time_availability_end,
                        match_end=match.time_scheduled_end,
                    )
                )

    @api.constrains("state")
    def _check_state(self):
        done_matches = self.filtered(lambda m: m.state == "done")
        for match in done_matches:
            match_mode = match.match_mode_id
            match_mode.get_points(match)
            for set_ in match.set_ids:
                match_mode._check_done_set_points(set_)

    @api.constrains("team_ids")
    def _check_teams(self):
        for match in self:
            teams = match.team_ids
            if len(teams) <= 1:
                raise exceptions.ValidationError(
                    match.env._("A good match needs at least 2 teams")
                )
            teams = list(teams)
            while teams:
                team = teams.pop()
                for other_team in teams:
                    other_team_components = other_team.component_ids
                    common_components = team.component_ids & other_team_components
                    if common_components:
                        common_components_names = common_components.mapped(
                            "display_name"
                        )
                        raise exceptions.ValidationError(
                            match.env._(
                                "Match %(match_name)s not valid:\n"
                                "Teams %(team_name} and {other_team_name)s have "
                                "common components (%(common_components_names)s).",
                                common_components_names=", ".join(
                                    common_components_names
                                ),
                                other_team_name=other_team.display_name,
                                team_name=team.display_name,
                                match_name=match.display_name,
                            )
                        )

    @api.constrains("tournament_id", "team_ids")
    def _check_tournament(self):
        for match in self:
            teams_tournaments = match.team_ids.tournament_id
            if len(teams_tournaments) > 1:
                raise exceptions.ValidationError(
                    match.env._(
                        "Match %(match_name)s not valid:\n"
                        "Teams from different tournaments.",
                        match_name=match.display_name,
                    )
                )
            teams_tournament = first(teams_tournaments)
            if teams_tournament and teams_tournament != match.tournament_id:
                raise exceptions.ValidationError(
                    match.env._(
                        "Match %(match_name)s not valid:\n"
                        "Teams not in tournament %(tourn_name)s.",
                        match_name=match.display_name,
                        tourn_name=match.tournament_id.display_name,
                    )
                )

    @api.constrains("winner_team_id", "team_ids")
    def _check_winner(self):
        for match in self:
            winner = match.winner_team_id
            if not winner:
                continue
            match_teams = match.team_ids
            if winner not in match_teams:
                raise exceptions.ValidationError(
                    match.env._(
                        "Match %(match_name)s not valid:\n"
                        "winner team %(team_name)s is not participating.",
                        match_name=match.display_name,
                        team_name=winner.display_name,
                    )
                )

    @api.depends(
        "state",
        "stats_ids.team_id",
        "stats_ids.won_sets_count",
    )
    def _compute_winner_team_id(self):
        for match in self:
            if match.state == "done":
                match_mode = match.match_mode_id
                winner_teams = match_mode.get_match_winner(match)
            else:
                winner_teams = self.env["event.tournament.team"].browse()
            match.winner_team_id = winner_teams

    def action_draft(self):
        self.ensure_one()
        self.update({"time_done": False, "state": "draft"})

    def action_done(self):
        self.ensure_one()
        if self.state == "done":
            raise exceptions.UserError(
                self.env._(
                    "Match %(match_name)s already done.", match_name=self.display_name
                )
            )
        self.update(
            {
                "time_done": fields.Datetime.now(),
                "state": "done",
            }
        )

        winner_teams = self.winner_team_id
        if not winner_teams:
            raise exceptions.UserError(
                self.env._(
                    "No-one won the match %(match_name)s.", match_name=self.display_name
                )
            )
        return True

    @api.depends("team_ids.name")
    def _compute_display_name(self):
        for match in self:
            teams = match.team_ids
            match.display_name = " vs ".join(teams.mapped("name"))

    @api.model_create_multi
    def create(self, vals_list):
        matches = super().create(vals_list)
        stats_model = self.env["event.tournament.match.team_stats"]
        for match in matches:
            match.stats_ids = stats_model.create_from_matches(match)
        return matches

    @api.depends(
        "match_mode_id.tie_break_number",
    )
    def _compute_set_ids(self):
        for match in self:
            existing_sets = match.set_ids
            if not existing_sets:
                mode = match.match_mode_id
                tie_break_number = mode.tie_break_number
                if tie_break_number:
                    sets_command = [
                        Command.create(
                            {
                                # + 1 for naming them 1, 2 instead of 0, 1
                                "name": str(s + 1),
                            }
                        )
                        for s in range(tie_break_number)
                    ]
                else:
                    sets_command = []
                sets = sets_command
            else:
                sets = existing_sets
            match.set_ids = sets
