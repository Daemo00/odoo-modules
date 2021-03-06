#  Copyright 2020 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import first
from odoo.tools.safe_eval import safe_eval


class EventTournamentTeam(models.Model):
    _name = "event.tournament.team"
    _description = "Tournament team"
    _rec_name = "name"
    _order = "matches_points desc, sets_won desc, points_ratio desc"

    event_id = fields.Many2one(related="tournament_id.event_id", readonly=True)
    tournament_id = fields.Many2one(
        comodel_name="event.tournament",
        string="Tournament",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(required=True)
    component_ids = fields.Many2many(
        comodel_name="event.registration",
        string="Components",
        copy=False,
    )
    match_ids = fields.Many2many(
        comodel_name="event.tournament.match", string="Matches", copy=False
    )
    match_count = fields.Integer(string="Match count", compute="_compute_match_count")
    points_ratio = fields.Float(compute="_compute_matches_points", store=True)
    points_done = fields.Float(compute="_compute_matches_points", store=True)
    points_taken = fields.Float(compute="_compute_matches_points", store=True)
    sets_won = fields.Integer(compute="_compute_matches_points", store=True)
    matches_points = fields.Integer(compute="_compute_matches_points", store=True)
    notes = fields.Text(string="Notes")

    _sql_constraints = [
        (
            "name_uniq_in_tournament",
            "unique (name, tournament_id)",
            "The name of the team must be unique in the tournament.",
        )
    ]

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.setdefault("name", _("%s (copy)") % (self.name or ""))
        return super().copy(default=default)

    @api.onchange("tournament_id")
    def onchange_tournament(self):
        components_domain = [
            ("event_id", "=", self.event_id.id),
            ("tournament_ids", "not in", self.tournament_id.id),
        ]
        matches_domain = [("tournament_id", "=", self.tournament_id.id)]
        return {
            "domain": {"component_ids": components_domain, "match_ids": matches_domain}
        }

    @api.depends("match_ids")
    def _compute_match_count(self):
        for team in self:
            team.match_count = len(team.match_ids)

    def set_team_domain(self, action):
        self.ensure_one()
        domain = action.get("domain") or "[]"
        domain = safe_eval(domain)
        domain.append(("team_ids", "in", self.ids))
        action.update(domain=domain)

    def action_view_matches(self):
        self.ensure_one()
        action = self.env.ref("event_tournament.event_tournament_match_action")
        action = action.read()[0]
        self.set_team_domain(action)
        return action

    @api.constrains("component_ids", "tournament_id")
    def constrain_components_event(self):
        for team in self:
            components = team.component_ids
            event = team.event_id
            if not components or not event:
                continue
            components_events = components.mapped("event_id")
            if len(components_events) > 1:
                raise ValidationError(
                    _(
                        "Team {team_name} not valid:\n"
                        "Components from different events."
                    ).format(team_name=team.display_name)
                )
            components_event = first(components_events)
            if components_event != event:
                raise ValidationError(
                    _(
                        "Team {team_name} not valid:\n"
                        "Components not in event {event_name}."
                    ).format(team_name=team.display_name, event_name=event.display_name)
                )

    @api.constrains("component_ids", "tournament_id")
    def constrain_components_tournament(self):
        for team in self:
            components = team.component_ids
            tournament = team.tournament_id
            if not components or not tournament:
                continue
            for other_team in tournament.team_ids - team:
                for component in components:
                    if component in other_team.component_ids:
                        raise ValidationError(
                            _(
                                "Tournament {tourn_name}, "
                                "team {team_name} not valid:\n"
                                "component {comp_name} is already in "
                                "team {other_team_name}."
                            ).format(
                                tourn_name=tournament.display_name,
                                team_name=team.display_name,
                                comp_name=component.display_name,
                                other_team_name=other_team.display_name,
                            )
                        )
            if (
                tournament.min_components
                and len(components) < tournament.min_components
            ):
                raise ValidationError(
                    _(
                        "Tournament {tourn_name}, "
                        "team {team_name} not valid:\n"
                        "tournament {tourn_name} requires "
                        "at least {min_comp} components per team."
                    ).format(
                        team_name=team.display_name,
                        tourn_name=tournament.display_name,
                        min_comp=tournament.min_components,
                    )
                )
            if (
                tournament.max_components
                and len(components) > tournament.max_components
            ):
                raise ValidationError(
                    _(
                        "Tournament {tourn_name}, "
                        "team {team_name} not valid:\n"
                        "tournament {tourn_name} requires "
                        "at most {max_comp} components per team."
                    ).format(
                        team_name=team.display_name,
                        tourn_name=tournament.display_name,
                        max_comp=tournament.max_components,
                    )
                )
            if tournament.min_components_female or tournament.min_components_male:
                if not all(c.gender for c in components):
                    raise ValidationError(
                        _(
                            "Tournament {tourn_name}, "
                            "team {team_name} not valid:\n"
                            "tournament {tourn_name} requires "
                            "a minimum of female (or male) components but "
                            "not all components have gender."
                        ).format(
                            team_name=team.display_name,
                            tourn_name=tournament.display_name,
                        )
                    )
                if tournament.min_components_female:
                    female_components = components.filtered(
                        lambda c: c.gender == "female"
                    )
                    if len(female_components) < tournament.min_components_female:
                        raise ValidationError(
                            _(
                                "Tournament {tourn_name}, "
                                "team {team_name} not valid:\n"
                                "tournament {tourn_name} requires at least "
                                "{min_female_comp} female components per team."
                            ).format(
                                team_name=team.display_name,
                                tourn_name=tournament.display_name,
                                min_female_comp=tournament.min_components_female,
                            )
                        )
                if tournament.min_components_male:
                    male_components = components.filtered(lambda c: c.gender == "male")
                    if len(male_components) < tournament.min_components_male:
                        raise ValidationError(
                            _(
                                "Tournament {tourn_name}, "
                                "team {team_name} not valid:\n"
                                "tournament {tourn_name} requires at least "
                                "{min_male_comp} male components per team."
                            ).format(
                                team_name=team.display_name,
                                tourn_name=tournament.display_name,
                                min_male_comp=tournament.min_components_male,
                            )
                        )

    @api.depends(
        lambda m: (
            "match_ids",
            "match_ids.state",
            "match_ids.match_mode_id",
            "match_ids.match_mode_id.result_ids",
        )
        + tuple("match_ids.line_ids.set_" + str(n) for n in range(1, 6))
    )
    def _compute_matches_points(self):
        for team in self:
            sets_lost = 0
            sets_won = 0
            points_done = 0
            points_taken = 0
            tournament_points = 0
            done_matches = team.match_ids.filtered(lambda m: m.state == "done")
            for match in done_matches:
                for match_team, sets_info in match.get_sets_info().items():
                    if team != match_team:
                        continue
                    sets_lost += sets_info[0]
                    sets_won += sets_info[1]
                    points_done += sets_info[2]
                    points_taken += sets_info[3]
                if match.match_mode_id:
                    tournament_points += match.match_mode_id.get_points(match)[team]

            team.sets_won = sets_won
            team.points_done = points_done
            team.points_taken = points_taken
            team.points_ratio = points_done / (points_taken or 1)
            team.matches_points = tournament_points

    def button_compute_matches_points(self):
        """Public method (callable from UI) for computing match's points."""
        self._compute_matches_points()
