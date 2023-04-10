#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account_partner_split.tests.common import TestCommon


class TestAccountPartnerSplit(TestCommon):
    def test_account_split_default(self):
        default_lines = self.split_account.partner_split_weight_ids
        self.assertEqual(default_lines[0].weight, 1)

    def test_account_split_one_expense(self):
        account = self.split_account
        self._add_expense(account, 100)

        totals = account.total_partner_split_ids
        total_partner_1 = totals.filtered_domain(
            [("partner_id", "=", self.partner_1.id)]
        )
        total_partner_2 = totals.filtered_domain(
            [("partner_id", "=", self.partner_2.id)]
        )
        self.assertEqual(
            total_partner_1.display_name, f"{self.partner_1.display_name} -25.0"
        )
        self.assertEqual(total_partner_1.amount, total_partner_2.amount)
        self.assertEqual(total_partner_1.amount, -25)
        total_partner_3 = totals.filtered_domain(
            [("partner_id", "=", self.partner_3.id)]
        )
        self.assertEqual(total_partner_3.amount, -50)

    def test_account_split_one_expense_one_payment(self):
        account = self.split_account
        line = self._add_expense(account, 100)
        self._add_payment(line, self.partner_1, 100)

        self.assertEqual(account.total_amount, 0)

        totals = account.total_partner_split_ids
        total_partner_1 = totals.filtered_domain(
            [("partner_id", "=", self.partner_1.id)]
        )
        self.assertEqual(total_partner_1.amount, 75)
        total_partner_2 = totals.filtered_domain(
            [("partner_id", "=", self.partner_2.id)]
        )
        self.assertEqual(total_partner_2.amount, -25)
        total_partner_3 = totals.filtered_domain(
            [("partner_id", "=", self.partner_3.id)]
        )
        self.assertEqual(total_partner_3.amount, -50)

    def test_account_split_one_expense_one_partial_payment(self):
        account = self.split_account
        line = self._add_expense(account, 100)
        self._add_payment(line, self.partner_3, 75)

        self.assertEqual(account.total_amount, -25)

        totals = account.total_partner_split_ids
        total_partner_1 = totals.filtered_domain(
            [("partner_id", "=", self.partner_1.id)]
        )
        self.assertEqual(total_partner_1.amount, -25)
        total_partner_2 = totals.filtered_domain(
            [("partner_id", "=", self.partner_2.id)]
        )
        self.assertEqual(total_partner_2.amount, -25)
        total_partner_3 = totals.filtered_domain(
            [("partner_id", "=", self.partner_3.id)]
        )
        self.assertEqual(total_partner_3.amount, 25)

    def test_account_split_one_expense_one_over_payment(self):
        account = self.split_account
        line = self._add_expense(account, 100)
        self._add_payment(line, self.partner_3, 150)

        self.assertEqual(account.total_amount, 50)

        totals = account.total_partner_split_ids
        total_partner_1 = totals.filtered_domain(
            [("partner_id", "=", self.partner_1.id)]
        )
        self.assertEqual(total_partner_1.amount, -25)
        total_partner_2 = totals.filtered_domain(
            [("partner_id", "=", self.partner_2.id)]
        )
        self.assertEqual(total_partner_2.amount, -25)
        total_partner_3 = totals.filtered_domain(
            [("partner_id", "=", self.partner_3.id)]
        )
        self.assertEqual(total_partner_3.amount, 100)

    def test_account_split_one_expense_multiple_payments(self):
        account = self.split_account
        line = self._add_expense(account, 100)
        self._add_payment(line, self.partner_2, 20)
        self._add_payment(line, self.partner_3, 30)

        self.assertEqual(account.total_amount, -50)

        totals = account.total_partner_split_ids
        total_partner_1 = totals.filtered_domain(
            [("partner_id", "=", self.partner_1.id)]
        )
        self.assertEqual(total_partner_1.amount, -25)
        total_partner_2 = totals.filtered_domain(
            [("partner_id", "=", self.partner_2.id)]
        )
        self.assertEqual(total_partner_2.amount, -5)
        total_partner_3 = totals.filtered_domain(
            [("partner_id", "=", self.partner_3.id)]
        )
        self.assertEqual(total_partner_3.amount, -20)
