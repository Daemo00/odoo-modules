#  Copyright 2020 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import Counter

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command, first
from odoo.osv import expression


class EventTournamentMatch(models.Model):
    _name = "event.tournament.match"
    _description = "Tournament match"
    _order = "time_scheduled_start"

    tournament_id = fields.Many2one(
        comodel_name="event.tournament",
        string="Tournament",
        required=True,
        states={"done": [("readonly", True)]},
    )
    match_mode_id = fields.Many2one(
        related="tournament_id.match_mode_id", states={"done": [("readonly", True)]}
    )
    court_id = fields.Many2one(
        comodel_name="event.tournament.court",
        string="Court",
        required=True,
        states={"done": [("readonly", True)]},
    )
    set_ids = fields.One2many(
        comodel_name="event.tournament.match.set",
        inverse_name="match_id",
        string="Sets",
        states={"done": [("readonly", True)]},
    )
    result_ids = fields.One2many(
        comodel_name="event.tournament.match.set.result",
        inverse_name="match_id",
        states={"done": [("readonly", True)]},
    )

    team_ids = fields.Many2many(
        comodel_name="event.tournament.team",
        states={"done": [("readonly", True)]},
    )
    component_ids = fields.Many2many(
        comodel_name="event.registration",
        compute="_compute_components",
        store=True,
        states={"done": [("readonly", True)]},
    )
    winner_team_id = fields.Many2one(
        comodel_name="event.tournament.team",
        string="Winner",
        states={"done": [("readonly", True)]},
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done")], default="draft"
    )
    time_scheduled_start = fields.Datetime(
        string="Scheduled start", states={"done": [("readonly", True)]}
    )
    time_scheduled_end = fields.Datetime(
        string="Scheduled end", states={"done": [("readonly", True)]}
    )
    time_done = fields.Datetime(
        states={
            "done": [
                ("readonly", True),
            ],
        },
    )

    @api.onchange("tournament_id")
    def onchange_tournament(self):
        event_domain = [("event_id", "=", self.tournament_id.event_id.id)]
        return {"domain": {"court_id": event_domain}}

    @api.depends("team_ids.component_ids")
    def _compute_components(self):
        for match in self:
            match.component_ids = match.team_ids.mapped("component_ids")

    @api.constrains("time_scheduled_start", "time_scheduled_end")
    def constrain_tournament_time(self):
        for match in self:
            tournament_start = match.tournament_id.start_datetime
            if (
                tournament_start
                and match.time_scheduled_start
                and tournament_start > match.time_scheduled_start
            ):
                raise ValidationError(
                    _(
                        "Match {match_name} not valid:\n"
                        "Tournament starts at {tournament_start} but "
                        "match starts at {match_start}."
                    ).format(
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
                raise ValidationError(
                    _(
                        "Match {match_name} not valid:\n"
                        "Tournament ends at {tournament_end} but "
                        "match ends at {match_end}."
                    ).format(
                        match_name=match.display_name,
                        tournament_end=tournament_end,
                        match_end=match.time_scheduled_end,
                    )
                )

    @api.constrains("time_scheduled_start", "time_scheduled_end", "component_ids")
    def constrain_contemporary(self):
        for match in self:
            contemporary_matches_domain = match.contemporary_match_domain()
            contemporary_matches = self.search(contemporary_matches_domain)
            contemporary_matches = contemporary_matches - match
            match_components = match.component_ids
            for cont_match in contemporary_matches:
                cont_match_components = cont_match.component_ids
                for cont_match_component in cont_match_components:
                    if cont_match_component in match_components:
                        raise ValidationError(
                            _(
                                "Match {match_name} not valid:\n"
                                "Component {comp_name} is already playing "
                                "in match {cont_match_name}."
                            ).format(
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
    def constrain_court(self):
        for match in self:
            if match.court_id not in match.tournament_id.court_ids:
                raise ValidationError(
                    _(
                        "Match {match_name} not valid:\n"
                        "Court {court_name} is not available for "
                        "tournament {tourn_name}."
                    ).format(
                        match_name=match.display_name,
                        court_name=match.court_id.display_name,
                        tourn_name=match.tournament_id.display_name,
                    )
                )

    @api.constrains("court_id", "time_scheduled_start", "time_scheduled_end")
    def constrain_court_time(self):
        for match in self:
            court = match.court_id
            overlapping_matches_domain = match.contemporary_match_domain()
            court_domain = [("court_id", "=", court.id)]
            overlapping_matches_domain.extend(court_domain)
            overlapping_matches = self.search(overlapping_matches_domain)
            overlapping_matches = overlapping_matches - match
            if overlapping_matches:
                overlapping_match = first(overlapping_matches)
                raise ValidationError(
                    _(
                        "Court {court_name} not valid:\n"
                        "match {match_name} is overlapping "
                        "{overlapping_match_name}."
                    ).format(
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
                raise ValidationError(
                    _(
                        "Match {match_name} not valid:\n"
                        "court {court_name} is available "
                        "from {court_start} but "
                        "match starts at {match_start}."
                    ).format(
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
                raise ValidationError(
                    _(
                        "Match {match_name} not valid:\n"
                        "court {court_name} is available "
                        "until {court_end} but "
                        "match ends at {match_end}."
                    ).format(
                        match_name=match.display_name,
                        court_name=court.display_name,
                        court_end=court.time_availability_end,
                        match_end=match.time_scheduled_end,
                    )
                )

    @api.constrains("team_ids")
    def constrain_teams(self):
        for match in self:
            teams = match.team_ids
            if len(teams) <= 1:
                raise ValidationError(_("A good match needs at least 2 teams"))
            teams = list(teams)
            while teams:
                team = teams.pop()
                for other_team in teams:
                    other_team_components = other_team.mapped("component_ids")
                    common_components = team.component_ids & other_team_components
                    if common_components:
                        common_components_names = common_components.mapped(
                            "display_name"
                        )
                        raise ValidationError(
                            _(
                                "Match {match_name} not valid:\n"
                                "Teams {team_name} and {other_team_name} have "
                                "common components ({common_components_names})."
                            ).format(
                                common_components_names=", ".join(
                                    common_components_names
                                ),
                                other_team_name=other_team.display_name,
                                team_name=team.display_name,
                                match_name=match.display_name,
                            )
                        )

    @api.constrains("tournament_id", "team_ids")
    def constrain_tournament(self):
        for match in self:
            teams_tournaments = match.team_ids.mapped("tournament_id")
            if len(teams_tournaments) > 1:
                raise ValidationError(
                    _(
                        "Match {match_name} not valid:\n"
                        "Teams from different tournaments."
                    ).format(match_name=match.display_name)
                )
            teams_tournament = first(teams_tournaments)
            if teams_tournament and teams_tournament != match.tournament_id:
                raise ValidationError(
                    _(
                        "Match {match_name} not valid:\n"
                        "Teams not in tournament {tourn_name}."
                    ).format(
                        match_name=match.display_name,
                        tourn_name=match.tournament_id.display_name,
                    )
                )

    @api.constrains("winner_team_id", "team_ids")
    def _constrain_winner(self):
        for match in self:
            if not match.winner_team_id:
                continue
            if match.winner_team_id not in match.team_ids:
                raise ValidationError(
                    _(
                        "Match {match_name} not valid:\n"
                        "winner team {team_name} is not participating."
                    ).format(
                        match_name=match.display_name,
                        team_name=match.winner_team_id.display_name,
                    )
                )

    def action_draft(self):
        self.ensure_one()
        self.update({"winner_team_id": False, "time_done": False, "state": "draft"})

    def action_done(self):
        self.ensure_one()
        if self.state == "done":
            raise UserError(
                _("Match {match_name} already done.").format(
                    match_name=self.display_name
                )
            )
        sets_info = self.get_sets_info()
        team_won_sets_dict = {
            team: sets_info[team]["won_sets"] for team in sets_info.keys()
        }
        max_won_sets = max(team_won_sets_dict.values())
        if not max_won_sets:
            raise UserError(
                _("No-one won a set in {match_name}.").format(
                    match_name=self.display_name
                )
            )
        winner_teams = self.winner_team_id.browse()
        for team, won_sets in team_won_sets_dict.items():
            if won_sets == max_won_sets:
                winner_teams |= team
        win_vals = {"time_done": fields.Datetime.now(), "state": "done"}

        winner_id = False
        if len(winner_teams) == 1:
            winner_id = winner_teams.id
        win_vals.update({"winner_team_id": winner_id})

        return self.update(win_vals)

    def name_get(self):
        res = []
        for match in self:
            teams = match.team_ids
            teams_names = teams.mapped("name")
            match_name = " vs ".join(teams_names)
            res.append((match.id, match_name))
        return res

    def get_sets_info(self):
        """
        Get the sets won by each team and their points done/taken.

        :return: A dictionary mapping involved teams to a tuple
            (sets lost, sets won, points done, points taken)
        """
        self.ensure_one()
        lost_sets = Counter()
        won_sets = Counter()
        done_points = Counter()
        taken_points = Counter()
        for set_ in self.set_ids:
            team_points_dict = {}
            for result in set_.result_ids:
                team_points_dict[result.team_id] = result.score
            points_list = team_points_dict.values()
            if not sum(points_list):
                # Set hasn't been played
                continue

            max_set_points = max(points_list)
            all_set_points = sum(points_list)
            for team, set_done_points in team_points_dict.items():
                done_points[team] += set_done_points
                taken_points[team] += all_set_points - set_done_points

            winner_teams_list = filter(
                lambda tp: tp[1] == max_set_points, team_points_dict.items()
            )
            winner_teams_list = list(dict(winner_teams_list).keys())
            if len(winner_teams_list) > 1:
                raise UserError(
                    _(
                        "Match {match_name}, Set {set_string}:\n"
                        "Ties are not allowed."
                    ).format(
                        match_name=self.display_name,
                        set_string=set_.display_name,
                    )
                )
            winner_team = winner_teams_list[0]
            for team in self.team_ids:
                if team == winner_team:
                    won_sets[team] += 1
                else:
                    lost_sets[team] += 1
        return {
            team: {
                "lost_sets": lost_sets[team],
                "won_sets": won_sets[team],
                "done_points": done_points[team],
                "taken_points": taken_points[team],
            }
            for team in self.team_ids
        }


class EventTournamentMatchSet(models.Model):
    _name = "event.tournament.match.set"
    _description = "Set of a Tournament match"
    _rec_name = "name"

    name = fields.Char()
    match_id = fields.Many2one(
        comodel_name="event.tournament.match", required=True, ondelete="cascade"
    )
    match_team_ids = fields.Many2many(
        related="match_id.team_ids",
        relation="event_tournament_set_team_rel",
        column1="set_id",
        column2="team_id",
        readonly=True,
        store=True,
    )
    result_ids = fields.One2many(
        comodel_name="event.tournament.match.set.result",
        inverse_name="set_id",
        readonly=False,
    )

    @api.model
    def _get_default_result_ids(self, match):
        match_teams = match.team_ids
        new_results = [
            Command.create(
                {
                    "team_id": team.id,
                }
            )
            for team in match_teams
        ]
        return new_results

    @api.model
    def default_get(self, fields_list):
        # The match is in the context, but it is not really missing
        fields_list.append("match_id")
        defaults = super().default_get(fields_list)
        if "result_ids" in fields_list:
            match_id = defaults.get("match_id")
            match = self.match_id.browse(match_id)
            new_results = self._get_default_result_ids(match)
            defaults["result_ids"] = new_results

        return defaults


class EventTournamentMatchSetResult(models.Model):
    _name = "event.tournament.match.set.result"
    _description = "Result of a Set of a Tournament match"

    match_id = fields.Many2one(
        related="set_id.match_id",
    )
    set_id = fields.Many2one(
        comodel_name="event.tournament.match.set", required=True, ondelete="cascade"
    )
    set_team_ids = fields.Many2many(
        related="set_id.match_team_ids",
        relation="event_tournament_result_team_rel",
        column1="result_id",
        column2="team_id",
        readonly=True,
        store=True,
    )
    team_id = fields.Many2one(
        comodel_name="event.tournament.team",
        required=True,
        ondelete="restrict",
        domain="[('id', 'in', set_team_ids)]",
    )
    score = fields.Integer()

    _sql_constraints = [
        (
            "unique_set_team",
            "UNIQUE(team_id, set_id)",
            "A team can only have one score in each set.",
        ),
    ]

    def name_get(self):
        names = [
            (
                result.id,
                f"{result.team_id.name}: {result.score}",
            )
            for result in self
        ]
        return names
