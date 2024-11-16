#  Copyright 2024 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Program(models.Model):
    _name = "appliance.usage.cost.appliance.program"
    _description = "Appliance Program"

    name = fields.Char(
        required=True,
    )
    duration = fields.Float(
        string="Duration (hours)",
    )
    appliance_id = fields.Many2one(
        comodel_name="appliance.usage.cost.appliance",
        required=True,
        ondelete="cascade",
    )
    utility_usage_ids = fields.One2many(
        comodel_name="appliance.usage.cost.appliance.program.utility.usage",
        inverse_name="program_id",
        string="Utility Usages",
    )
