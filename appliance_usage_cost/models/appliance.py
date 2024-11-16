#  Copyright 2024 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Appliance(models.Model):
    _name = "appliance.usage.cost.appliance"
    _description = "Appliance"

    name = fields.Char(
        required=True,
    )
    brand = fields.Char()
    image = fields.Binary()
    model = fields.Char()
    program_ids = fields.One2many(
        comodel_name="appliance.usage.cost.appliance.program",
        inverse_name="appliance_id",
        string="Programs",
    )
