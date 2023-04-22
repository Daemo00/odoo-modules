#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tools import float_round


class PartnerTotalSplit(models.Model):
    _name = "account_partner_split.partner_total_split"
    _description = "Partner total split"
    _rec_name = "display_name"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
    )
    amount = fields.Monetary(
        compute="_compute_amount",
        store=True,
    )
    abs_amount = fields.Monetary(
        string="Absolute Amount",
        compute="_compute_abs_amount",
        store=True,
    )
    credit_amount = fields.Monetary()
    debit_amount = fields.Monetary()
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
    )
    line_split_account_id = fields.Many2one(
        related="split_account_line_id.split_account_id",
        string="Account",
        store=True,
    )
    line_tag_ids = fields.Many2many(
        compute="_compute_line_tag_ids",
        comodel_name="account_partner_split.account.line.tag",
        relation="account_partner_split_total_line_tag_rel",
        column1="total_line_id",
        column2="tag_id",
        string="Tags",
        store=True,
    )
    line_invoice_date = fields.Datetime(
        related="split_account_line_id.invoice_date",
        string="Date",
        store=True,
    )
    split_account_line_id = fields.Many2one(
        comodel_name="account_partner_split.account.line",
        string="Split Account Line",
        store=True,
    )
    split_account_id = fields.Many2one(
        comodel_name="account_partner_split.account",
        string="Split Account for total",
        ondelete="cascade",
    )

    @api.depends(
        "credit_amount",
        "debit_amount",
    )
    def _compute_amount(self):
        for total in self:
            total.amount = total.credit_amount - total.debit_amount

    @api.depends(
        "split_account_line_id.tag_ids",
    )
    def _compute_line_tag_ids(self):
        for total_line in self:
            line = total_line.split_account_line_id
            total_line.line_tag_ids = line.tag_ids

    @api.depends(
        "amount",
    )
    def _compute_abs_amount(self):
        for line in self:
            line.abs_amount = abs(line.amount)

    def name_get(self):
        name_template = _("{partner} {amount}")
        res = []
        for partner_total_split in self:
            currency = partner_total_split.currency_id
            if currency:
                rounding = currency.rounding
            else:
                rounding = 0.01
            amount = partner_total_split.amount
            name = name_template.format(
                partner=partner_total_split.partner_id.display_name,
                amount=float_round(amount, precision_rounding=rounding),
            )
            res.append((partner_total_split.id, name))
        return res
