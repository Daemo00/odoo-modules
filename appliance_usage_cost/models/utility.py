#  Copyright 2024 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Utility(models.Model):
    _name = "appliance.usage.cost.utility"
    _description = "Utility"

    name = fields.Char(
        required=True,
        translate=True,
    )
    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        required=True,
    )
