#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import Command, _, fields, models
from odoo.tools import float_round


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
    )
    split_account_id = fields.Many2one(
        comodel_name="account_partner_split.account",
        string="Split Account",
        ondelete="cascade",
    )

    def generate_payment(self):
        self.ensure_one()
        currency = self.currency_id
        if currency:
            rounding = currency.rounding
        else:
            rounding = 0.01

        account = self.split_account_id
        account.line_ids = [
            Command.create(
                {
                    "name": _("{from_partner} gives {amount} to {to_partner}").format(
                        from_partner=self.from_partner_id.display_name,
                        amount=float_round(self.amount, precision_rounding=rounding),
                        to_partner=self.to_partner_id.display_name,
                    ),
                    "is_payment": True,
                    # Credit only on 'from'
                    "paying_partner_split_ids": [
                        Command.create(
                            {
                                "partner_id": self.from_partner_id.id,
                                "amount": self.amount,
                            }
                        ),
                    ],
                    # Debit only on 'to'
                    "partner_split_weight_ids": [
                        Command.create(
                            {
                                "partner_id": self.to_partner_id.id,
                                "weight": 1,
                            }
                        ),
                    ],
                }
            ),
        ]
        self.unlink()
