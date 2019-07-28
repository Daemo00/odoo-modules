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
        required=True)
    component_ids = fields.Many2many(
        comodel_name='event.registration',
        string="Components")
    match_ids = fields.Many2many(
        comodel_name='event.tournament.match',
        string="Matches")

    @api.onchange('tournament_id')
    def onchange_tournament(self):
        event_domain = [('event_id', '=', self.tournament_id.event_id.id)]
        tournament_domain = [('tournament_id', '=', self.tournament_id.id)]
        return {
            'domain': {
                'component_ids': event_domain,
                'match_ids': tournament_domain}}

    @api.constrains('component_ids', 'match_ids', 'tournament_id')
    def constrain_tournament(self):
        for team in self:
            components_events = team.component_ids.mapped('event_id')
            if len(components_events) > 1:
                raise ValidationError(_("Components from different events"))
            components_event = first(components_events)
            if components_event \
                    and components_event != team.tournament_id.event_id:
                raise ValidationError(_("Components not in selected event"))

            teams_events = team.match_ids.mapped('tournament_id.event_id')
            if len(teams_events) > 1:
                raise ValidationError(_("Teams from different events"))
            teams_event = first(teams_events)
            if teams_event \
                    and teams_event != team.tournament_id.event_id:
                raise ValidationError(_("Teams not in selected event"))

    @api.multi
    def button_win(self):
        """This is clicked inside the tree of a match"""
        self.ensure_one()
        params = self.env.context['params']
        match = self.env[params['model']].browse(params['id'])
        match.action_win(self)
