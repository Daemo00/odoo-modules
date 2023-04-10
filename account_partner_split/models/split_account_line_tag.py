#  Copyright 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SplitAccountLineTag(models.Model):
    _name = "account_partner_split.account.line.tag"
    _description = "Split Account Line Tag"

    name = fields.Char()
