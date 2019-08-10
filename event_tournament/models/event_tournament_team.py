#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.fields import first


class EventTournamentTeam (models.Model):
    _name = 'event.tournament.team'
    _description = "Tournament team"
    _rec_name = 'name'
    _order = 'points_ratio desc'

    event_id = fields.Many2one(
        related='tournament_id.event_id',
        readonly=True)
    tournament_id = fields.Many2one(
        comodel_name='event.tournament',
        string="Tournament",
        required=True,
        ondelete='cascade')
    name = fields.Char(
        required=True)
    component_ids = fields.Many2many(
        comodel_name='event.registration',
        string="Components")
    match_ids = fields.Many2many(
        comodel_name='event.tournament.match',
        string="Matches")
    points_ratio = fields.Float(
        compute='_compute_points_ratio',
        store=True)

    @api.onchange('tournament_id')
    def onchange_tournament(self):
        components_domain = [
            ('event_id', '=', self.event_id.id),
            ('tournament_ids', 'not in', self.tournament_id.id)]
        matches_domain = [('tournament_id', '=', self.tournament_id.id)]
        return {
            'domain': {
                'component_ids': components_domain,
                'match_ids': matches_domain}}

    @api.constrains('component_ids', 'tournament_id')
    def constrain_components(self):
        for team in self:
            components = team.component_ids
            if not components:
                continue
            team.check_components_event(components, team.event_id)
            team.check_components_tournament(components, team.tournament_id)

    @api.multi
    def check_components_event(self, components, event):
        self.ensure_one()
        components_events = components.mapped('event_id')
        if len(components_events) > 1:
            raise ValidationError(_(
                "Team {team_name} not valid:\n"
                "Components from different events")
                .format(
                    team_name=self.display_name))
        components_event = first(components_events)
        if components_event != event:
            raise ValidationError(_(
                "Team {team_name} not valid:\n"
                "Components not in event {event_name}.")
                .format(
                    team_name=self.display_name,
                    event_name=event.display_name))

    @api.multi
    def check_components_tournament(self, components, tournament):
        self.ensure_one()
        for other_team in tournament.team_ids - self:
            for component in components:
                if component in other_team.component_ids:
                    raise ValidationError(_(
                        "Team {team_name} not valid:\n"
                        "component {comp_name} is already in "
                        "team {other_team_name}.")
                        .format(
                            team_name=self.display_name,
                            comp_name=component.display_name,
                            other_team_name=other_team.display_name))
        if tournament.min_components \
                and len(components) < tournament.min_components:
            raise ValidationError(_(
                "Team {team_name} not valid:\n"
                "tournament {tourn_name} requires "
                "at least {min_comp} components per team.")
                .format(
                    team_name=self.display_name,
                    tourn_name=tournament.display_name,
                    min_comp=tournament.min_components))
        if tournament.max_components \
                and len(components) > tournament.max_components:
            raise ValidationError(_(
                "Team {team_name} not valid:\n"
                "tournament {tourn_name} requires "
                "at least {max_comp} components per team.")
                .format(
                    team_name=self.display_name,
                    tourn_name=tournament.display_name,
                    max_comp=tournament.max_components))
        if tournament.min_components_female or tournament.min_components_male:
            if not all(c.gender for c in components):
                raise ValidationError(_(
                    "Team {team_name} not valid:\n"
                    "tournament {tourn_name} requires "
                    "a minimum of female (or male) components but "
                    "not all components have gender.")
                    .format(
                        team_name=self.display_name,
                        tourn_name=tournament.display_name))
            if tournament.min_components_female:
                female_components = components.filtered(
                    lambda c: c.gender == 'female')
                if len(female_components) > tournament.min_components_female:
                    raise ValidationError(_(
                        "Team {team_name} not valid:\n"
                        "tournament {tourn_name} requires at least "
                        "{min_female_comp} female components per team.")
                        .format(
                            team_name=self.display_name,
                            tourn_name=tournament.display_name,
                            min_female_comp=tournament.min_components_female))
            if tournament.min_components_male:
                male_components = components.filtered(
                    lambda c: c.gender == 'male')
                if len(male_components) > tournament.min_components_male:
                    raise ValidationError(_(
                        "Team {team_name} not valid:\n"
                        "tournament {tourn_name} requires at least "
                        "{min_male_comp} male components per team.")
                        .format(
                            team_name=self.display_name,
                            tourn_name=tournament.display_name,
                            min_male_comp=tournament.min_components_male))

    @api.multi
    @api.depends('match_ids.line_ids.points_done')
    def _compute_points_ratio(self):
        for team in self:
            points_done = 0
            points_taken = 0
            for match in team.match_ids:
                for line in match.line_ids:
                    if line.team_id == team:
                        points_done += line.points_done
                    else:
                        points_taken += line.points_done
            team.points_ratio = points_done / (points_taken or 1)
