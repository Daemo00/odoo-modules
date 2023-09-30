#  Copyright 2020 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command, first
from odoo.models import NewId
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
        states={"done": [("readonly", True)]},
    )
    match_mode_id = fields.Many2one(
        related="tournament_id.match_mode_id", states={"done": [("readonly", True)]}
    )
    court_id = fields.Many2one(
        comodel_name="event.tournament.court",
        string="Court",
        required=True,
        domain="[('event_id', '=', event_id)]",
        states={"done": [("readonly", True)]},
    )
    set_ids = fields.One2many(
        comodel_name="event.tournament.match.set",
        inverse_name="match_id",
        compute="_compute_set_ids",
        store=True,
        readonly=False,
        string="Sets",
        domain="[('match_id', '=', id)]",
        states={"done": [("readonly", True)]},
    )
    result_ids = fields.One2many(
        comodel_name="event.tournament.match.set.result",
        inverse_name="match_id",
        states={"done": [("readonly", True)]},
    )

    team_ids = fields.Many2many(
        comodel_name="event.tournament.team",
        relation="event_tournament_match_team_rel",
        domain="[('tournament_id', '=', tournament_id)]",
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
        compute="_compute_winner_team_id",
        store=True,
        help="Computed only on done matches.",
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
    stats_ids = fields.One2many(
        comodel_name="event.tournament.match.team_stats",
        inverse_name="match_id",
    )

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
            winner = match.winner_team_id
            if not winner:
                continue
            match_teams = match.team_ids
            if winner not in match_teams:
                raise ValidationError(
                    _(
                        "Match {match_name} not valid:\n"
                        "winner team {team_name} is not participating."
                    ).format(
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
            raise UserError(
                _("Match {match_name} already done.").format(
                    match_name=self.display_name
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
            raise UserError(
                _("No-one won the match {match_name}.").format(
                    match_name=self.display_name
                )
            )
        return True

    def name_get(self):
        res = []
        for match in self:
            teams = match.team_ids
            teams_names = teams.mapped("name")
            match_name = " vs ".join(teams_names)
            res.append((match.id, match_name))
        return res

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
                        for s in range(tie_break_number + 1)
                    ]
                else:
                    sets_command = []
                sets = sets_command
            else:
                sets = existing_sets
            match.set_ids = sets


class EventTournamentMatchTeamStats(models.Model):
    _name = "event.tournament.match.team_stats"
    _description = "Team stats for a match"

    match_id = fields.Many2one(
        comodel_name="event.tournament.match",
        ondelete="cascade",
        required=True,
    )
    team_id = fields.Many2one(
        comodel_name="event.tournament.team",
        ondelete="cascade",
        required=True,
    )

    lost_set_ids = fields.Many2many(
        comodel_name="event.tournament.match.set",
        relation="event_tournament_match_team_stats_lost_set_rel",
        string="Lost sets",
        compute="_compute_sets",
        store=True,
    )
    lost_sets_count = fields.Integer(
        compute="_compute_sets",
        store=True,
    )

    won_set_ids = fields.Many2many(
        comodel_name="event.tournament.match.set",
        relation="event_tournament_match_team_stats_won_set_rel",
        string="Won sets",
        compute="_compute_sets",
        store=True,
    )
    won_sets_count = fields.Integer(
        compute="_compute_sets",
        store=True,
    )

    done_points = fields.Integer(
        compute="_compute_points",
        store=True,
    )
    taken_points = fields.Integer(
        compute="_compute_points",
        store=True,
    )

    sets_ratio = fields.Float(compute="_compute_sets_ratio", store=True, digits=(16, 5))
    points_ratio = fields.Float(
        compute="_compute_points_ratio", store=True, digits=(16, 5)
    )

    tournament_points = fields.Integer(
        compute="_compute_tournament_points",
        help="Only computed for done matches.",
        store=True,
    )

    @api.model
    def create_from_matches(self, matches):
        stats = self.create(
            [
                {
                    "match_id": match.id,
                    "team_id": team.id,
                }
                for match in matches
                for team in match.team_ids
            ]
        )
        return stats

    @api.depends(
        "match_id.set_ids.result_ids.score",
    )
    def _compute_points(self):
        for stat in self:
            team = stat.team_id
            match = stat.match_id

            sets = match.set_ids
            results = sets.result_ids
            match_points = sum(results.mapped("score"))

            team_results = results.filtered(lambda result: result.team_id == team)
            team_points = sum(team_results.mapped("score"))

            stat.done_points = team_points
            stat.taken_points = match_points - team_points

    @api.depends(
        "match_id.state",
        "match_id.match_mode_id.result_ids.won_sets",
        "match_id.match_mode_id.result_ids.lost_sets",
        "match_id.match_mode_id.result_ids.win_points",
        "match_id.match_mode_id.result_ids.lose_points",
        "match_id.stats_ids.won_sets_count",
        "match_id.stats_ids.lost_sets_count",
        "team_id",
    )
    def _compute_tournament_points(self):
        for stat in self:
            match = stat.match_id
            tournament_points = 0
            if match.state == "done":
                team = stat.team_id
                match_mode = match.match_mode_id
                if match_mode:
                    match_points = match_mode.get_points(match)
                    tournament_points = match_points.get(team, 0)

            stat.tournament_points = tournament_points

    @api.depends(
        "match_id.state",
        "team_id",
        "match_id.set_ids.winner_team_id",
    )
    def _compute_sets(self):
        set_model = self.env["event.tournament.match.set"]
        for stat in self:
            match = stat.match_id
            team = stat.team_id

            lost_sets = won_sets = set_model.browse()
            if match.state == "done":
                sets = match.set_ids
                for set_ in sets:
                    set_winners = set_.winner_team_id
                    if team in set_winners:
                        won_sets |= set_
                    else:
                        lost_sets |= set_

            stat.won_set_ids = won_sets
            stat.won_sets_count = len(won_sets)
            stat.lost_set_ids = lost_sets
            stat.lost_sets_count = len(lost_sets)

    @api.model
    def calculate_ratio(self, won, lost):
        return won / (lost or 0.1)

    def get_points_ratio(self):
        done_points = sum(self.mapped("done_points"))
        taken_points = sum(self.mapped("taken_points"))
        points_ratio = self.calculate_ratio(done_points, taken_points)
        return points_ratio

    def get_sets_ratio(self):
        won_sets_count = sum(self.mapped("won_sets_count"))
        lost_sets_count = sum(self.mapped("lost_sets_count"))
        sets_ratio = self.calculate_ratio(won_sets_count, lost_sets_count)
        return sets_ratio

    @api.depends(
        "done_points",
        "taken_points",
    )
    def _compute_points_ratio(self):
        for stat in self:
            stat.points_ratio = stat.get_points_ratio()

    @api.depends(
        "lost_sets_count",
        "won_sets_count",
    )
    def _compute_sets_ratio(self):
        for stat in self:
            stat.sets_ratio = stat.get_sets_ratio()


class EventTournamentMatchSet(models.Model):
    _name = "event.tournament.match.set"
    _description = "Set of a Tournament match"
    _rec_name = "name"

    name = fields.Char(
        required=True,
    )
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
        compute="_compute_result_ids",
        store=True,
        readonly=False,
    )
    winner_team_id = fields.Many2many(
        comodel_name="event.tournament.team",
        relation="event_tournament_set_winner_team_rel",
        column1="set_id",
        column2="team_id",
        compute="_compute_winner_team_id",
        store=True,
        help="Only computed on done matches.",
    )
    is_tie_break = fields.Boolean(
        compute="_compute_is_tie_break",
        store=True,
    )

    @api.depends(
        "match_id.match_mode_id.tie_break_number",
    )
    def _compute_is_tie_break(self):
        for set_ in self:
            match = set_.match_id
            match_mode = match.match_mode_id
            tie_break_number = match_mode.tie_break_number
            sets = match.set_ids
            is_tie_break = (
                len(sets) > tie_break_number and sets[tie_break_number] == set_
            )
            set_.is_tie_break = is_tie_break

    @api.depends(
        "match_id.match_mode_id.win_set_points",
        "match_id.match_mode_id.win_set_break_points",
        "match_id.match_mode_id.win_tie_break_points",
        "match_id.state",
        "is_tie_break",
        "result_ids.score",
        "match_team_ids",
    )
    def _compute_winner_team_id(self):
        for set_ in self:
            match = set_.match_id
            if match.state == "done":
                match_mode = match.match_mode_id
                winner_team = match_mode.get_set_winner(set_)
            else:
                winner_team = self.env["event.tournament.team"].browse()
            set_.winner_team_id = winner_team

    @api.depends(
        "match_id.team_ids",
    )
    def _compute_result_ids(self):
        for set_ in self:
            match = set_.match_id
            needing_result_teams = match.team_ids
            existing_results = set_.result_ids
            results_command = []
            if existing_results:
                for existing_result in existing_results:
                    team = existing_result.team_id
                    if team not in match.team_ids:
                        # Otherwise when a team is removed from the match,
                        # the result cannot be deleted
                        # (tries to empty its set_id before deleting it)
                        if not isinstance(match.id, NewId):
                            # A team has been removed: remove its results
                            results_command.append(
                                Command.delete(existing_result.id),
                            )
                    else:
                        needing_result_teams -= team

            results_command.extend(
                [
                    Command.create(
                        {
                            "team_id": team.id,
                        }
                    )
                    for team in needing_result_teams
                ]
            )
            set_.result_ids = results_command


class EventTournamentMatchSetResult(models.Model):
    _name = "event.tournament.match.set.result"
    _description = "Result of a Set of a Tournament match"

    tournament_id = fields.Many2one(
        related="match_id.tournament_id",
    )
    court_id = fields.Many2one(
        related="match_id.court_id",
    )
    match_mode_id = fields.Many2one(
        related="match_id.match_mode_id",
    )
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
        string="Match Teams",
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
