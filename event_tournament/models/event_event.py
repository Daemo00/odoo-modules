#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EventEvent(models.Model):
    _inherit = "event.event"

    tournament_ids = fields.One2many(
        comodel_name="event.tournament", inverse_name="event_id", string="Tournaments"
    )
    court_ids = fields.One2many(
        comodel_name="event.tournament.court", inverse_name="event_id", string="Courts"
    )
