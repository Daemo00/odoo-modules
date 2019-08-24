#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EventCourt(models.Model):
    _name = 'event.tournament.court'
    _description = "Court for tournaments"

    event_id = fields.Many2one(
        comodel_name='event.event')
    name = fields.Char(
        string="Name")
    time_availability_start = fields.Datetime(
        string="Availability start")
    time_availability_end = fields.Datetime(
        string="Availability end")