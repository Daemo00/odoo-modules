#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import Counter

from odoo import Command, api, fields, models
from odoo.tools import float_compare


class Account(models.Model):
    _name = "account_partner_split.account"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Split Account"

    name = fields.Char()
    partner_split_weight_ids = fields.One2many(
        comodel_name="account_partner_split.partner_split_weight",
        inverse_name="split_account_id",
        string="Partner weights",
        help="Default values for Lines",
    )
    total_partner_split_ids = fields.One2many(
        comodel_name="account_partner_split.partner_total_split",
        inverse_name="split_account_id",
        string="Total Partners",
        compute="_compute_total_partner_split_ids",
        store=True,
    )
    partner_payment_ids = fields.One2many(
        comodel_name="account_partner_split.partner_payment",
        inverse_name="split_account_id",
        string="Payments",
    )
    line_ids = fields.One2many(
        comodel_name="account_partner_split.account.line",
        inverse_name="split_account_id",
        string="Lines",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
    )
    total_amount = fields.Monetary(
        string="Total",
        help="Excluding internal payments",
        compute="_compute_total_amount",
        store=True,
    )

    @api.depends(
        "line_ids.is_payment",
        "line_ids.amount",
    )
    def _compute_total_amount(self):
        for account in self:
            lines = account.line_ids.filtered(lambda line: not line.is_payment)
            if lines:
                total_amounts_paid = lines.mapped("amount")
                total_amount = sum(total_amounts_paid)
            else:
                total_amount = 0
            account.total_amount = total_amount

    def _get_amount_by_partner(self):
        """Group amounts of each line by partner."""
        self.ensure_one()
        account_total = {}

        lines = self.line_ids
        line_totals = lines.total_partner_split_ids
        partners = line_totals.partner_id
        for partner in partners:
            partner_totals = line_totals.filtered(
                lambda t, p=partner: t.partner_id == p
            )
            partner_credits = partner_totals.mapped("credit_amount")
            if partner_credits:
                partner_credit = sum(partner_credits)
            else:
                partner_credit = 0
            partner_debits = partner_totals.mapped("debit_amount")
            if partner_debits:
                partner_debit = sum(partner_debits)
            else:
                partner_debit = 0

            account_total[partner] = {
                "credit_amount": partner_credit,
                "debit_amount": partner_debit,
            }

        return account_total

    @api.depends(
        "line_ids.total_partner_split_ids.amount",
        "line_ids.total_partner_split_ids.partner_id",
    )
    def _compute_total_partner_split_ids(self):
        for account in self:
            account_total = account._get_amount_by_partner()
            old_totals = account.total_partner_split_ids
            new_totals = self.env[
                "account_partner_split.account.line"
            ]._get_updated_totals(old_totals, account_total)
            account.total_partner_split_ids = new_totals

    def generate_payment_proposals(self):
        self.ensure_one()
        currency = self.currency_id
        if currency:
            rounding = currency.rounding
        else:
            rounding = 0.01

        totals = self.total_partner_split_ids

        debtors = totals.filtered(
            lambda t: float_compare(t.amount, 0, precision_rounding=rounding) < 0
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
            payment_lines = [
                Command.create(
                    {
                        "from_partner_id": payment[0].id,
                        "to_partner_id": payment[1].id,
                        "amount": payment[2],
                    }
                )
                for payment in payments
            ]
            self.partner_payment_ids = payment_lines

    def action_view_report(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account_partner_split.partner_total_split_action"
        )
        action["domain"] = [
            ("line_split_account_id", "=", self.id),
        ]
        action["context"] = {
            "search_default_group_by_line_invoice_date": True,
            "search_default_group_by_partner_id": True,
            "fill_temporal": False,
        }
        return action
