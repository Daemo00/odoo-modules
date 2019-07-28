#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class EventTournamentMatch(models.Model):
    _name = 'event.tournament'
    _description = "Tournament"
    _rec_name = 'name'

    name = fields.Char(
        required=True)
    event_id = fields.Many2one(
        comodel_name='event.event',
        string="Event")
    match_ids = fields.One2many(
        comodel_name='event.tournament.match',
        inverse_name='tournament_id',
        string="Matches")
    team_ids = fields.One2many(
        comodel_name='event.tournament.team',
        inverse_name='tournament_id',
        string="Teams")
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('done', "Done")])

    @api.multi
    def action_done(self):
        for tournament in self:
            tournament.match_ids.action_done()
