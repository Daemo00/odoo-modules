#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import Command, _, fields, models


class PartnerPayment(models.Model):
    _name = "account_partner_split.partner_payment"
    _description = "Partner split"

    from_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="From partner",
        required=True,
    )
    to_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="To partner",
        required=True,
    )
    amount = fields.Monetary(
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        required=True,
        compute="_compute_currency_id",
        precompute=True,
        readonly=False,
        store=True,
    )
    account_id = fields.Many2one(
        comodel_name="account_partner_split.account",
        string="Account",
        ondelete="cascade",
        required=True,
    )

    _sql_constraints = [
        (
            "no_self_payment",
            "CHECK(from_partner_id != to_partner_id)",
            "From and To Partner must be different",
        ),
    ]

    def _compute_currency_id(self):
        company_currency = self.env.company.currency_id
        for payment in self:
            payment.currency_id = (
                payment.account_id.currency_id
                or payment.currency_id
                or company_currency
            )

    def _prepare_account_line_values(self):
        self.ensure_one()
        from_partner = self.from_partner_id
        to_partner = self.to_partner_id
        amount = self.amount

        payment_currency = self.currency_id
        account_currency = self.account_id.currency_id
        if payment_currency != account_currency:
            amount = payment_currency._convert(
                amount,
                account_currency,
                self.env.company,
                fields.Date.today(),
            )

        return {
            "name": _(
                "%(from_partner)s gives %(amount)s to %(to_partner)s",
                from_partner=from_partner.name,
                amount=amount,
                to_partner=to_partner.name,
            ),
            "currency_id": self.currency_id.id,
            "partner_line_ids": [
                Command.create(
                    {
                        "partner_id": from_partner.id,
                        "amount": amount,
                    }
                ),
                Command.create(
                    {
                        "partner_id": to_partner.id,
                        "amount": -amount,
                    }
                ),
            ],
        }

    def generate_payment(self):
        """Convert this payment to an account line."""
        self.ensure_one()
        self.account_id.line_ids = [
            Command.create(self._prepare_account_line_values()),
        ]
        self.unlink()
