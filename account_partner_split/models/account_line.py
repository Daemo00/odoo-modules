#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models


class AccountLine(models.Model):
    _name = "account_partner_split.account.line"
    _description = "Split Account Line"
    _order = "date, id"

    name = fields.Char()
    date = fields.Datetime(
        default=fields.Datetime.now,
    )
    account_id = fields.Many2one(
        comodel_name="account_partner_split.account",
        string="Account",
        required=True,
        ondelete="cascade",
    )
    partner_weight_ids = fields.One2many(
        comodel_name="account_partner_split.partner_weight",
        inverse_name="account_line_id",
        string="Partner Weights",
    )
    partner_line_ids = fields.One2many(
        comodel_name="account_partner_split.partner.amount",
        inverse_name="account_line_id",
        string="Amounts contributed by partners",
    )
    total_partner_line_ids = fields.One2many(
        comodel_name="account_partner_split.partner.amount",
        inverse_name="total_account_line_id",
        string="Totals by partner",
        compute="_compute_total_partner_line_ids",
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        compute="_compute_currency_id",
        precompute=True,
        required=True,
        store=True,
        readonly=False,
    )
    amount = fields.Monetary(
        string="Cost for this line",
    )
    paid_amount = fields.Monetary(
        string="Amount paid",
        help="Amount paid by partners.",
        compute="_compute_paid_amount",
        store=True,
    )
    to_pay_amount = fields.Monetary(
        string="Amount to pay",
        help="Amount to be paid by partners yet.",
        compute="_compute_to_pay_amount",
        store=True,
    )

    @api.depends(
        "account_id",
    )
    def _compute_currency_id(self):
        company_currency = self.env.company.currency_id
        for line in self:
            line.currency_id = (
                line.account_id.currency_id or line.currency_id or company_currency
            )

    @api.depends(
        "partner_line_ids.amount",
    )
    def _compute_paid_amount(self):
        for line in self:
            line.paid_amount = sum(
                line.partner_line_ids.mapped("amount"),
            )

    @api.depends(
        "amount",
        "paid_amount",
    )
    def _compute_to_pay_amount(self):
        for line in self:
            line.to_pay_amount = line.amount - line.paid_amount

    def split_by_weight(self, amount):
        """Split `amount` in parts based on partner weights.

        Return a dictionary mapping each partner to its share.
        """
        return self.partner_weight_ids.split_by_weight(amount)

    def _get_partner_to_owed_amount(self):
        """Group amounts owed by partner."""
        self.ensure_one()
        partner_to_to_pay_amount = self.split_by_weight(self.amount)
        partner_to_paid_amount = self.partner_line_ids._group_amount_by_partner()

        partners = set(partner_to_to_pay_amount.keys()).union(
            set(partner_to_paid_amount.keys())
        )
        return {
            partner: partner_to_paid_amount.get(partner, 0)
            - partner_to_to_pay_amount.get(partner, 0)
            for partner in partners
        }

    @api.depends(
        "partner_line_ids.partner_id",
        "partner_line_ids.amount",
        "partner_weight_ids.partner_id",
        "partner_weight_ids.weight",
        "amount",
    )
    def _compute_total_partner_line_ids(self):
        for line in self:
            partner_to_owed_amount = line._get_partner_to_owed_amount()
            line.total_partner_line_ids = (
                line.total_partner_line_ids._get_update_commands(
                    partner_to_owed_amount,
                    default_values=dict(
                        total_account_line_id=line.id,
                    ),
                )
            )

    @api.onchange(
        "account_id",
    )
    def onchange_account_id(self):
        self.ensure_one()
        self.partner_weight_ids = [
            Command.clear(),
        ] + [
            Command.create(
                {
                    "partner_id": partner_weight.partner_id.id,
                    "weight": partner_weight.weight,
                }
            )
            for partner_weight in self.account_id.partner_weight_ids
        ]

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.account_id and not line.partner_weight_ids:
                line.onchange_account_id()
        return lines
