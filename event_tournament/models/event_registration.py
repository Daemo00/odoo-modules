#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    tournament_team_ids = fields.Many2many(
        comodel_name='event.tournament.team',
        string="Teams")
