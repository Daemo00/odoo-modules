#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.fields import first


class EventTournamentTeam (models.Model):
    _name = 'event.tournament.team'
    _description = "Tournament team"
    _rec_name = 'name'

    name = fields.Char(
        required=True)
    tournament_id = fields.Many2one(
        comodel_name='event.tournament',
        string="Tournament",
        required=True,
        ondelete='cascade')
    match_ids = fields.Many2many(
        comodel_name='event.tournament.match',
        string="Matches")
    event_id = fields.Many2one(
        related='tournament_id.event_id',
        readonly=True)
    component_ids = fields.Many2many(
        comodel_name='event.registration',
        string="Components")

    @api.onchange('tournament_id')
    def onchange_tournament(self):
        event_domain = [('event_id', '=', self.event_id.id)]
        tournament_domain = [('tournament_id', '=', self.tournament_id.id)]
        return {
            'domain': {
                'component_ids': event_domain,
                'match_ids': tournament_domain}}

    @api.constrains('tournament_id', 'match_ids')
    def constrain_matches(self):
        for team in self:
            teams_tournaments = team.match_ids.mapped('tournament_id')
            if len(teams_tournaments) > 1:
                raise ValidationError(_("Teams from different tournaments"))
            teams_tournament = first(teams_tournaments)
            if teams_tournament != team.tournament_id:
                raise ValidationError(_("Teams not in selected tournament"))

    @api.constrains('component_ids', 'match_ids', 'tournament_id')
    def constrain_components(self):
        for team in self:
            components_events = team.component_ids.mapped('event_id')
            if len(components_events) > 1:
                raise ValidationError(_("Components from different events"))
            components_event = first(components_events)
            if components_event != team.event_id:
                raise ValidationError(_("Components not in selected event"))
