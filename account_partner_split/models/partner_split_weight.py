#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import Counter

from odoo import _, fields, models


class PartnerSplitWeight(models.Model):
    _name = "account_partner_split.partner_split_weight"
    _description = "Partner split"
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
    split_account_line_id = fields.Many2one(
        comodel_name="account_partner_split.account.line",
        string="Split Account Line",
        ondelete="cascade",
    )
    split_account_id = fields.Many2one(
        comodel_name="account_partner_split.account",
        string="Split Account",
        ondelete="cascade",
    )

    def compute_split_parts(self, amount):
        """Split `amount` in parts in `self`.

        Return a dictionary mapping each partner to its share.
        """
        amount_by_partner = Counter()
        if self:
            total_weight = sum(map(abs, self.mapped("weight")))
            amount_part = amount / total_weight
            for partner_split in self:
                partner = partner_split.partner_id
                weight = partner_split.weight
                partner_amount = weight * amount_part
                amount_by_partner_split = Counter(
                    {
                        partner: partner_amount,
                    }
                )
                # Using update instead of += to keep negative values
                amount_by_partner.update(amount_by_partner_split)
        return amount_by_partner

    def name_get(self):
        name_template = _("{partner} has weight {weight}")
        res = list()
        for partner_weight in self:
            weight = partner_weight.weight
            name = name_template.format(
                partner=partner_weight.partner_id.display_name,
                weight=weight,
            )
            res.append((partner_weight.id, name))
        return res
