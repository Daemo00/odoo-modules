#  Copyright 2020 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import Counter

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import first
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
    line_ids = fields.One2many(
        comodel_name="event.tournament.match.line",
        inverse_name="match_id",
        string="Teams",
        states={"done": [("readonly", True)]},
    )
    team_ids = fields.Many2many(
        comodel_name="event.tournament.team",
        compute="_compute_teams",
        inverse="_inverse_teams",
        store=True,
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
        string="Time done", states={"done": [("readonly", True)]}
    )

    @api.onchange("tournament_id")
    def onchange_tournament(self):
        event_domain = [("event_id", "=", self.tournament_id.event_id.id)]
        return {"domain": {"court_id": event_domain}}

    @api.depends("line_ids.team_id")
    def _compute_teams(self):
        for match in self:
            match.team_ids = match.line_ids.mapped("team_id")

    def _inverse_teams(self):
        for match in self:
            team_lines = match.line_ids.mapped("team_id")
            lines_vals = list()
            for team in match.team_ids:
                if team not in team_lines:
                    lines_vals.append({"match_id": match.id, "team_id": team.id})
            match.line_ids.create(lines_vals)

    @api.depends("team_ids.component_ids")
    def _compute_components(self):
        for match in self:
            match.component_ids = match.team_ids.mapped("component_ids")

    @api.constrains("time_scheduled_start", "time_scheduled_end", "component_ids")
    def constrain_time(self):
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
        domain = list()
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
        sets_won_dict = {team: sets_info[team][1] for team in sets_info.keys()}
        max_sets_won = max(sets_won_dict.values())
        if not max_sets_won:
            raise UserError(
                _("No-one won a set in {match_name}.").format(
                    match_name=self.display_name
                )
            )
        winner_teams = self.winner_team_id.browse()
        for team, sets_won in sets_won_dict.items():
            if sets_won == max_sets_won:
                winner_teams |= team
        win_vals = dict({"time_done": fields.Datetime.now(), "state": "done"})

        winner_id = False
        if len(winner_teams) == 1:
            winner_id = winner_teams.id
        win_vals.update({"winner_team_id": winner_id})

        return self.update(win_vals)

    def name_get(self):
        res = list()
        for match in self:
            teams_names = match.team_ids.mapped("name")
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
        set_fields = ["set_" + str(n) for n in range(1, 6)]
        sets_lost = Counter()
        sets_won = Counter()
        points_done = Counter()
        points_taken = Counter()
        for set_field in set_fields:
            set_points = dict()
            for line in self.line_ids:
                set_points[line.team_id] = getattr(line, set_field)
            if not sum(set_points.values()):
                # Set hasn't been played
                continue
            max_set_points = max(set_points.values())
            all_set_points = sum(set_points.values())
            for team, set_points_done in set_points.items():
                points_done[team] += set_points_done
                points_taken[team] += all_set_points - set_points_done

            set_winners = filter(lambda tp: tp[1] == max_set_points, set_points.items())
            set_winners = list(dict(set_winners).keys())
            if len(set_winners) > 1:
                raise UserError(
                    _(
                        "Match {match_name}, {set_string}:\n" "Ties are not allowed."
                    ).format(
                        match_name=self.display_name,
                        set_string=self.line_ids._fields[set_field]._description_string(
                            self.env
                        ),
                    )
                )
            set_winner = set_winners[0]
            for team in self.team_ids:
                if team == set_winner:
                    sets_won[team] += 1
                else:
                    sets_lost[team] += 1
        return {
            team: (
                sets_lost[team],
                sets_won[team],
                points_done[team],
                points_taken[team],
            )
            for team in self.team_ids
        }


class EventTournamentMatchLine(models.Model):
    _name = "event.tournament.match.line"
    _description = "Tournament match line"
    _rec_name = "team_id"

    match_id = fields.Many2one(
        comodel_name="event.tournament.match", required=True, ondelete="cascade"
    )
    team_id = fields.Many2one(
        comodel_name="event.tournament.team", required=True, ondelete="cascade"
    )
    set_1 = fields.Integer()
    set_2 = fields.Integer()
    set_3 = fields.Integer()
    set_4 = fields.Integer()
    set_5 = fields.Integer()
