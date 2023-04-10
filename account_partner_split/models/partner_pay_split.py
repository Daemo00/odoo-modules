#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import Counter

from odoo import _, fields, models
from odoo.tools import float_round


class PartnerPaySplit(models.Model):
    _name = "account_partner_split.partner_pay_split"
    _description = "Partner pay split"
    _rec_name = "display_name"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
    )
    amount = fields.Monetary(
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
    )
    split_account_line_id = fields.Many2one(
        comodel_name="account_partner_split.account.line",
        string="Split Account Line",
        required=True,
        ondelete="cascade",
    )

    def _get_amount_by_partner(self):
        amount_by_partner = Counter()
        for paying_line in self:
            partner = paying_line.partner_id
            paid_amount = paying_line.amount
            existing_amount = amount_by_partner.get(partner, 0)
            amount = existing_amount + paid_amount
            amount_by_partner[partner] = amount
        return amount_by_partner

    def name_get(self):
        name_template = _("{partner} pays {amount}")
        res = list()
        for partner_split in self:
            currency = partner_split.currency_id
            if currency:
                rounding = currency.rounding
            else:
                rounding = 0.01
            name = name_template.format(
                partner=partner_split.partner_id.display_name,
                amount=float_round(partner_split.amount, precision_rounding=rounding),
            )
            res.append((partner_split.id, name))
        return res
