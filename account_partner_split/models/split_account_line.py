#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import Command, api, fields, models


class AccountLine(models.Model):
    _name = "account_partner_split.account.line"
    _description = "Split Account Line"
    _order = "invoice_date, id"

    name = fields.Char()
    invoice_date = fields.Datetime(
        string="Date",
        default=fields.Datetime.now,
    )
    accounting_date = fields.Datetime()
    split_account_id = fields.Many2one(
        comodel_name="account_partner_split.account",
        string="Split Account",
        required=True,
        ondelete="cascade",
    )
    partner_split_weight_ids = fields.One2many(
        comodel_name="account_partner_split.partner_split_weight",
        inverse_name="split_account_line_id",
        string="Partner Weights",
    )
    paying_partner_split_ids = fields.One2many(
        comodel_name="account_partner_split.partner_pay_split",
        inverse_name="split_account_line_id",
        string="Paying Partners",
        required=True,
    )
    total_partner_split_ids = fields.One2many(
        comodel_name="account_partner_split.partner_total_split",
        inverse_name="split_account_line_id",
        string="Total Partners",
        compute="_compute_total_partner_split_ids",
        store=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
    )
    paid_amount = fields.Monetary(
        compute="_compute_paid_amount",
        store=True,
    )
    to_pay_amount = fields.Monetary()
    amount = fields.Monetary(
        compute="_compute_amount",
        store=True,
    )
    is_payment = fields.Boolean(
        string="Internal Payment",
        help="Payment among partners in the same account, " "not counted for totals",
    )
    tag_ids = fields.Many2many(
        comodel_name="account_partner_split.account.line.tag",
        relation="account_partner_split_line_tag_rel",
        column1="line_id",
        column2="tag_id",
        string="Tags",
    )

    @api.depends(
        "paying_partner_split_ids.amount",
    )
    def _compute_paid_amount(self):
        for line in self:
            pay_lines = line.paying_partner_split_ids
            if pay_lines:
                amounts_paid = pay_lines.mapped("amount")
                amount = sum(amounts_paid)
            else:
                amount = 0
            line.paid_amount = amount

    @api.depends(
        "paid_amount",
        "to_pay_amount",
    )
    def _compute_amount(self):
        for line in self:
            line.amount = line.paid_amount - line.to_pay_amount

    def _get_amount_to_share(self):
        to_pay = self.to_pay_amount
        paid = self.paid_amount
        if to_pay:
            amount_to_pay = to_pay
        elif paid:
            amount_to_pay = paid
        else:
            amount_to_pay = 0
        return amount_to_pay

    def _get_amount_by_partner(self):
        """Group amounts owed by partner."""
        self.ensure_one()
        amount_by_partner = {}

        # Subtract owed amounts
        amount_to_share = self._get_amount_to_share()
        amount_to_pay_by_partner = self.partner_split_weight_ids.compute_split_parts(
            amount_to_share
        )

        # Add paid amounts
        amount_paid_by_partner = self.paying_partner_split_ids._get_amount_by_partner()

        partners = set(amount_to_pay_by_partner.keys()).union(
            set(amount_paid_by_partner.keys())
        )
        for partner in partners:
            debit = amount_to_pay_by_partner.get(partner, 0)
            credit = amount_paid_by_partner.get(partner, 0)
            amount_by_partner[partner] = {
                "credit_amount": credit,
                "debit_amount": debit,
            }

        return amount_by_partner

    @api.model
    def _get_updated_totals(self, old_totals, amount_by_partner):
        if amount_by_partner:
            # Remove totals for partners not in new totals
            old_totals_to_remove = old_totals.filtered(
                lambda t: t.partner_id not in amount_by_partner.keys()
            )
            new_totals = [
                Command.unlink(old_total_to_remove.id)
                for old_total_to_remove in old_totals_to_remove
            ]

            # Create/Update totals for partners in new totals
            for partner, amounts in amount_by_partner.items():
                credit = amounts["credit_amount"]
                debit = amounts["debit_amount"]
                existing_partner_total = old_totals.filtered(
                    lambda t, p=partner: t.partner_id == p
                )
                if not existing_partner_total:
                    # Create total if there is an amount for the partner
                    partner_total = Command.create(
                        {
                            "partner_id": partner.id,
                            "credit_amount": credit,
                            "debit_amount": debit,
                        }
                    )
                else:
                    # Update total if there is an amount for the partner
                    partner_total = Command.update(
                        existing_partner_total.id,
                        {
                            "credit_amount": credit,
                            "debit_amount": debit,
                        },
                    )
                new_totals.append(partner_total)
        else:
            new_totals = [
                Command.clear(),
            ]
        return new_totals

    @api.depends(
        "paying_partner_split_ids.partner_id",
        "paying_partner_split_ids.amount",
        "partner_split_weight_ids.partner_id",
        "partner_split_weight_ids.weight",
        "amount",
    )
    def _compute_total_partner_split_ids(self):
        for line in self:
            amount_by_partner = line._get_amount_by_partner()
            new_totals = line._get_updated_totals(
                line.total_partner_split_ids,
                amount_by_partner,
            )
            line.total_partner_split_ids = new_totals

    @api.onchange(
        "split_account_id",
    )
    def onchange_split_account_id(self):
        # Propagate partner split values from account
        self.ensure_one()
        account = self.split_account_id
        account_split_lines = account.partner_split_weight_ids
        partner_split_weight_ids = [
            Command.clear(),
        ]
        if account_split_lines:
            partner_split_weight_ids += [
                Command.create(
                    {
                        "partner_id": account_split_line.partner_id.id,
                        "weight": account_split_line.weight,
                    }
                )
                for account_split_line in account_split_lines
            ]
        self.partner_split_weight_ids = partner_split_weight_ids
