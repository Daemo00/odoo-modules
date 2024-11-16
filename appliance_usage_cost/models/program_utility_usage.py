#  Copyright 2024 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProgramUtilityUsage(models.Model):
    _name = "appliance.usage.cost.appliance.program.utility.usage"
    _description = "Usage of Utility for Program"

    program_id = fields.Many2one(
        comodel_name="appliance.usage.cost.appliance.program",
        required=True,
        ondelete="cascade",
    )
    utility_id = fields.Many2one(
        comodel_name="appliance.usage.cost.utility",
        required=True,
        ondelete="cascade",
    )
    quantity = fields.Float(
        string="Consumption (per cycle)",
        required=True,
    )
    utility_uom_id = fields.Many2one(
        related="utility_id.uom_id",
        readonly=True,
    )

    _sql_constraints = [
        (
            "uniq_program_utility",
            "UNIQUE(program_id, utility_id)",
            "A utility can only be consumed once for each program",
        ),
    ]
