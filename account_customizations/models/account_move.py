#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    custom_account_ids = fields.Many2many(
        comodel_name="account.account",
        compute="_compute_custom_account_ids",
        store=True,
    )

    @api.depends(
        "line_ids.account_id",
    )
    def _compute_custom_account_ids(self):
        for move in self:
            move.custom_account_ids = move.line_ids.account_id
