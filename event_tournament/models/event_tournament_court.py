#  Copyright 2020 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class EventCourt(models.Model):
    _name = "event.tournament.court"
    _description = "Court for tournaments"

    event_id = fields.Many2one(comodel_name="event.event")
    sequence = fields.Integer()
    name = fields.Char()
    time_availability_start = fields.Datetime(string="Availability start")
    time_availability_end = fields.Datetime(string="Availability end")

    _sql_constraints = [
        (
            "name_uniq_in_event",
            "unique (name, event_id)",
            "The name of the court must be unique in the event.",
        )
    ]

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.setdefault("name", _("%s (copy)") % (self.name or ""))
        return super().copy(default=default)

    @api.onchange("event_id")
    def onchange_event_id(self):
        if self.event_id:
            self.time_availability_start = self.event_id.date_begin
            self.time_availability_end = self.event_id.date_end
