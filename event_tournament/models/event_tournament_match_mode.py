#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class EventTournamentMatchModeLine(models.Model):
    _name = 'event.tournament.match.mode.result'
    _description = 'Match mode result'

    mode_id = fields.Many2one(
        comodel_name='event.tournament.match.mode')
    team_1_result = fields.Integer()
    team_1_points = fields.Integer()
    team_2_result = fields.Integer()
    team_2_points = fields.Integer()


class EventTournamentMatchMode(models.Model):
    _name = 'event.tournament.match.mode'
    _description = 'Match mode'

    name = fields.Char()
    result_ids = fields.One2many(
        comodel_name='event.tournament.match.mode.result',
        inverse_name='mode_id')
