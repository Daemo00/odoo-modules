#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, tests
from odoo.tests import Form


class TestCommon(tests.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        partner_model = cls.env["res.partner"]
        partner_1_id, _ = partner_model.name_create("Test partner 1")
        cls.partner_1 = partner_model.browse(partner_1_id)
        partner_2_id, _ = partner_model.name_create("Test partner 2")
        cls.partner_2 = partner_model.browse(partner_2_id)
        partner_3_id, _ = partner_model.name_create("Test partner 3")
        cls.partner_3 = partner_model.browse(partner_3_id)

        split_account_form = Form(cls.env["account_partner_split.account"])
        split_account_form.name = "Test account"
        with split_account_form.partner_split_weight_ids.new() as default_split:
            default_split.partner_id = cls.partner_1
        with split_account_form.partner_split_weight_ids.new() as default_split:
            default_split.partner_id = cls.partner_2
        with split_account_form.partner_split_weight_ids.new() as default_split:
            default_split.partner_id = cls.partner_3
            default_split.weight = 2
        cls.split_account = split_account_form.save()

    def _add_expense(self, account, amount):
        """Expense shared among default partners."""
        account_form = Form(account)
        with account_form.line_ids.new() as line:
            line.split_account_id = account
            line.to_pay_amount = amount
        account = account_form.save()
        line = account.line_ids[-1]
        return line

    def _add_payment(self, line, partner, amount):
        """`partner` pays `amount` of `line`."""
        line_form = Form(line)
        with line_form.paying_partner_split_ids.new() as payment:
            payment.partner_id = partner
            payment.amount = amount
        return line_form.save()

    def _assign_only_to(self, line, partners=None):
        """Share `line` among `partners`."""
        if partners is None:
            partners = self.env["res.partner"].browse()

        weights = [
            Command.clear(),
        ]
        for partner in partners:
            weights.append(
                Command.create(
                    {
                        "partner_id": partner.id,
                    }
                )
            )
        line.partner_split_weight_ids = weights
