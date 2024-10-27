#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.fields import Command
from odoo.tools import float_round


class PartnerAmount(models.Model):
    _name = "account_partner_split.partner.amount"
    _description = "Partner and amount"

    total_account_id = fields.Many2one(
        comodel_name="account_partner_split.account",
        string="Total Account",
        ondelete="cascade",
    )
    account_line_id = fields.Many2one(
        comodel_name="account_partner_split.account.line",
        string="Account Line",
        ondelete="cascade",
    )
    account_id = fields.Many2one(
        related="account_line_id.account_id",
        readonly=True,
        store=True,
    )
    total_account_line_id = fields.Many2one(
        comodel_name="account_partner_split.account.line",
        string="Total Account Line",
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
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
    credit = fields.Monetary(
        help="How much Partner is owed for Account Line.",
    )
    debit = fields.Monetary(
        help="How much Partner owes for Account Line.",
    )
    amount = fields.Monetary(
        compute="_compute_amount",
        inverse="_inverse_amount",
        store=True,
        required=True,
    )
    abs_amount = fields.Monetary(
        compute="_compute_abs_amount",
        store=True,
    )
    date = fields.Datetime(
        compute="_compute_date",
        store=True,
        readonly=False,
    )

    _sql_constraints = [
        (
            "check_credit_debit",
            "CHECK(credit * debit = 0)",
            "Credit or Debit must be 0",
        ),
    ]

    @api.depends(
        "account_line_id.date",
        "total_account_line_id.date",
    )
    def _compute_date(self):
        for partner_amount in self:
            partner_amount.date = (
                partner_amount.date
                or partner_amount.account_line_id.date
                or partner_amount.total_account_line_id.date
            )

    def _compute_currency_id(self):
        company_currency = self.env.company.currency_id
        for partner_line in self:
            partner_line.currency_id = (
                partner_line.account_line_id.currency_id
                or partner_line.currency_id
                or company_currency
            )

    @api.depends(
        "credit",
        "debit",
    )
    def _compute_amount(self):
        for partner_line in self:
            partner_line.amount = partner_line.credit - partner_line.debit

    def _inverse_amount(self):
        for partner_line in self:
            amount = partner_line.amount
            if partner_line.currency_id.compare_amounts(amount, 0) > 0:
                credit, debit = amount, 0
            else:
                credit, debit = 0, amount
            partner_line.update(
                {
                    "credit": credit,
                    "debit": debit,
                }
            )

    @api.depends(
        "amount",
    )
    def _compute_abs_amount(self):
        for partner_line in self:
            partner_line.abs_amount = abs(partner_line.amount)

    def _group_amount_by_partner(self):
        """Group amount of partner lines by partner."""
        partner_to_amount = {}
        for partner in self.partner_id:
            partner_lines = self.filtered(lambda pl, p=partner: pl.partner_id == p)
            partner_to_amount[partner] = sum(partner_lines.mapped("amount"))
        return partner_to_amount

    def _get_update_commands(self, partner_to_amount, default_values=None):
        """Update `self` to reflect amounts shared as in `partner_to_amount`.

        Return list of Commands.
        """
        if partner_to_amount:
            # Remove totals for partners not in new totals
            old_totals_to_remove = self.filtered(
                lambda t: t.partner_id not in partner_to_amount.keys()
            )
            new_totals = [
                Command.unlink(old_total_to_remove.id)
                for old_total_to_remove in old_totals_to_remove
            ]

            # Create/Update totals for partners in new totals
            for partner, amount in partner_to_amount.items():
                existing_partner_total = self.filtered(
                    lambda t, p=partner: t.partner_id == p
                )
                if not existing_partner_total:
                    # Create total if there is an amount for the partner
                    partner_total = Command.create(
                        dict(
                            {
                                "partner_id": partner.id,
                                "amount": amount,
                            },
                            **(default_values or {}),
                        )
                    )
                else:
                    # Update total if there is an amount for the partner
                    partner_total = Command.update(
                        existing_partner_total.id,
                        {
                            "amount": amount,
                        },
                    )
                new_totals.append(partner_total)
        else:
            new_totals = [
                Command.clear(),
            ]
        return new_totals

    @api.depends(
        "partner_id.name",
        "amount",
        "currency_id.rounding",
    )
    def _compute_display_name(self):
        for partner_line in self:
            currency_digits = partner_line.currency_id.decimal_places
            partner_line.display_name = _(
                "%(partner)s: %(amount)+g",
                partner=partner_line.partner_id.name,
                amount=float_round(
                    partner_line.amount,
                    precision_digits=currency_digits,
                ),
            )
