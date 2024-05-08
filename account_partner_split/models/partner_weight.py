#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, fields, models


class PartnerWeight(models.Model):
    _name = "account_partner_split.partner_weight"
    _description = "Partner weight"
    _rec_name = "display_name"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
    )
    weight = fields.Integer(
        default=1,
        required=True,
    )
    account_line_id = fields.Many2one(
        comodel_name="account_partner_split.account.line",
        string="Split Account Line",
        ondelete="cascade",
    )
    account_id = fields.Many2one(
        comodel_name="account_partner_split.account",
        string="Split Account",
        ondelete="cascade",
    )

    def name_get(self):
        return [
            (
                partner_weight.id,
                (
                    _(
                        "%(partner)s has weight %(weight)s",
                        partner=partner_weight.partner_id.name,
                        weight=partner_weight.weight,
                    )
                ),
            )
            for partner_weight in self
        ]

    def split_by_weight(self, amount):
        """Split `amount` in parts based on the weights in `self`.

        Return a dictionary mapping each partner to its share.
        """
        partner_to_amount = {}
        total_weight = sum(self.mapped("weight")) or 1
        amount_part = amount / total_weight
        for partner in self.partner_id:
            partner_weight = self.filtered(lambda pw, p=partner: pw.partner_id == p)
            partner_to_amount[partner_weight.partner_id] = (
                partner_weight.weight * amount_part
            )
        return partner_to_amount
