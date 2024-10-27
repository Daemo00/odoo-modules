#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import Counter

from odoo import Command, api, fields, models
from odoo.tools import float_compare


class Account(models.Model):
    _name = "account_partner_split.account"
    _description = "Split Account"

    name = fields.Char(
        required=True,
    )
    partner_weight_ids = fields.One2many(
        comodel_name="account_partner_split.partner_weight",
        inverse_name="account_id",
        string="Partner weights",
        help="Default values for lines",
    )
    total_partner_line_ids = fields.Many2many(
        comodel_name="account_partner_split.partner.amount",
        relation="account_split_partner_amount_rel",
        string="Totals by partner",
        compute="_compute_total_partner_line_ids",
        store=True,
    )
    partner_payment_ids = fields.One2many(
        comodel_name="account_partner_split.partner_payment",
        inverse_name="account_id",
        string="Payments",
    )
    line_ids = fields.One2many(
        comodel_name="account_partner_split.account.line",
        inverse_name="account_id",
        string="Lines",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        required=True,
        default=lambda model: model.env.company.currency_id,
    )
    amount = fields.Monetary(
        compute="_compute_amount",
        store=True,
    )
    paid_amount = fields.Monetary(
        compute="_compute_paid_amount",
        store=True,
    )

    @api.depends(
        "line_ids.amount",
    )
    def _compute_amount(self):
        for account in self:
            account.amount = sum(account.line_ids.mapped("amount"))

    @api.depends(
        "line_ids.paid_amount",
    )
    def _compute_paid_amount(self):
        for account in self:
            account.paid_amount = sum(account.line_ids.mapped("paid_amount"))

    @api.depends(
        "line_ids.total_partner_line_ids.partner_id",
        "line_ids.total_partner_line_ids.amount",
    )
    def _compute_total_partner_line_ids(self):
        for account in self:
            partner_to_amount = (
                account.line_ids.total_partner_line_ids._group_amount_by_partner()
            )
            account.total_partner_line_ids = (
                account.total_partner_line_ids._get_update_commands(
                    partner_to_amount,
                    default_values=dict(
                        total_account_id=account.id,
                    ),
                )
            )

    def generate_payment_proposals(self):
        self.ensure_one()
        rounding = self.currency_id.rounding

        totals = self.total_partner_line_ids

        debtors = totals.filtered(
            lambda t, r=rounding: float_compare(t.amount, 0, precision_rounding=r) < 0
        )
        debtors = debtors.sorted(key=lambda t: -t.amount)
        creditors = totals - debtors
        creditors = creditors.sorted(key=lambda t: t.amount)

        debtors = Counter({debtor.partner_id: -debtor.amount for debtor in debtors})
        creditors = Counter(
            {creditor.partner_id: creditor.amount for creditor in creditors}
        )

        payments = []
        for creditor in creditors:
            for debtor, debit_amount in debtors.items():
                credit_amount = creditors.get(creditor, 0)
                debit_amount = debtors.get(debtor, 0)
                paid_amount = min(credit_amount, debit_amount)
                if float_compare(paid_amount, 0, precision_rounding=rounding) > 0:
                    payments.append((debtor, creditor, paid_amount))
                    creditors[creditor] -= paid_amount
                    debtors[debtor] -= paid_amount

        if payments:
            self.partner_payment_ids = [
                Command.create(
                    {
                        "from_partner_id": payment[0].id,
                        "to_partner_id": payment[1].id,
                        "amount": payment[2],
                    }
                )
                for payment in payments
            ]

    def action_view_report(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account_partner_split.partner_amount_action"
        )
        action["domain"] = [
            ("account_id", "=", self.id),
        ]
        action["context"] = {
            "search_default_group_by_account_line_id": True,
            "search_default_group_by_partner_id": True,
            "fill_temporal": False,
        }
        # Set graph as first
        view_modes = action["view_mode"].split(",")
        action["view_mode"] = ",".join(
            sorted(view_modes, key=lambda vm: 1 if vm == "graph" else -1, reverse=True)
        )
        return action
