#  Copyright 2020 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import first
from odoo.tools.safe_eval import safe_eval


class EventTournamentTeam(models.Model):
    _name = "event.tournament.team"
    _description = "Tournament team"
    _rec_name = "name"

    sequence = fields.Integer()
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
        relation="event_tournament_team_component_rel",
        column1="component_id",
        column2="team_id",
        domain="[" "('event_id', '=', event_id)," "]",
    )
    match_ids = fields.Many2many(
        comodel_name="event.tournament.match",
        string="Matches",
        copy=False,
        domain="[" "('tournament_id', '=', tournament_id)," "]",
    )
    match_count = fields.Integer(
        compute="_compute_match_count",
    )
    done_points = fields.Integer(compute="_compute_stats", store=True)
    taken_points = fields.Integer(compute="_compute_stats", store=True)
    won_set_ids = fields.Many2many(
        comodel_name="event.tournament.match.set",
        compute="_compute_stats",
        relation="event_tournament_team_won_set_rel",
        column1="team_id",
        column2="set_id",
        store=True,
    )
    won_sets_count = fields.Integer(compute="_compute_stats", store=True)
    lost_set_ids = fields.Many2many(
        comodel_name="event.tournament.match.set",
        compute="_compute_stats",
        relation="event_tournament_team_lost_set_rel",
        column1="team_id",
        column2="set_id",
        store=True,
    )
    lost_sets_count = fields.Integer(compute="_compute_stats", store=True)
    tournament_points = fields.Integer(compute="_compute_stats", store=True)
    notes = fields.Text()
    stats_ids = fields.One2many(
        comodel_name="event.tournament.match.team_stats",
        inverse_name="team_id",
    )
    sets_ratio = fields.Float(compute="_compute_sets_ratio", store=True, digits=(16, 5))
    points_ratio = fields.Float(
        compute="_compute_points_ratio", store=True, digits=(16, 5)
    )

    @api.depends(
        "stats_ids.done_points",
        "stats_ids.taken_points",
    )
    def _compute_points_ratio(self):
        for team in self:
            team.points_ratio = team.stats_ids.get_points_ratio()

    @api.depends(
        "stats_ids.lost_sets_count",
        "stats_ids.won_sets_count",
    )
    def _compute_sets_ratio(self):
        for team in self:
            team.sets_ratio = team.stats_ids.get_sets_ratio()

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
            if not components:
                continue

            # Check all the components are from the same event
            components_events = components.mapped("event_id")
            if len(components_events) > 1:
                raise ValidationError(
                    _(
                        "Team {team_name} not valid:\n"
                        "Components from different events."
                    ).format(team_name=team.display_name)
                )

            event = team.event_id
            if not event:
                continue

            # Check all the components are from the team's event
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
            if not tournament.share_components:
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
        "stats_ids.done_points",
        "stats_ids.taken_points",
        "stats_ids.won_set_ids",
        "stats_ids.won_sets_count",
        "stats_ids.lost_set_ids",
        "stats_ids.lost_sets_count",
        "stats_ids.tournament_points",
    )
    def _compute_stats(self):
        for team in self:
            stats = team.stats_ids
            if stats:
                done_points = sum(stats.mapped("done_points"))
                taken_points = sum(stats.mapped("taken_points"))
                won_sets_count = sum(stats.mapped("won_sets_count"))
                lost_sets_count = sum(stats.mapped("lost_sets_count"))
                tournament_points = sum(stats.mapped("tournament_points"))
            else:
                done_points = 0
                taken_points = 0
                won_sets_count = 0
                lost_sets_count = 0
                tournament_points = 0

            team.done_points = done_points
            team.taken_points = taken_points
            team.won_set_ids = stats.won_set_ids
            team.won_sets_count = won_sets_count
            team.lost_set_ids = stats.lost_set_ids
            team.lost_sets_count = lost_sets_count
            team.tournament_points = tournament_points
