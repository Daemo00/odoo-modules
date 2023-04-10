#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.account_partner_split.tests.common import TestCommon


class TestAccountPartnerSplit(TestCommon):
    def test_night_out(self):
        """Simulate 3 partners going out.
        Everything is always paid for.
        """
        night_out = self.split_account
        partner_1 = self.partner_1
        partner_2 = self.partner_2
        partner_3 = self.partner_3

        default_lines = night_out.partner_split_weight_ids
        default_partner_1 = default_lines.filtered_domain(
            [("partner_id", "=", partner_1.id)]
        )
        self.assertEqual(default_partner_1.weight, 1)
        default_partner_2 = default_lines.filtered_domain(
            [("partner_id", "=", partner_2.id)]
        )
        self.assertEqual(default_partner_2.weight, 1)
        # This one pays for two
        default_partner_3 = default_lines.filtered_domain(
            [("partner_id", "=", partner_3.id)]
        )
        self.assertEqual(default_partner_3.weight, 2)

        # Drinks:
        # 1 pays 50 but owes 12.5: is owed 37.5
        # 2 owes 12.5
        # 3 owes 25
        drinks = self._add_expense(night_out, 50)
        self._add_payment(drinks, partner_1, 50)

        # Dinner:
        # 1 owes 50
        # 2 owes 50
        # 3 pays 200 but owes 100: is owed 100
        dinner = self._add_expense(night_out, 200)
        self._add_payment(dinner, partner_3, 200)

        # More drinks:
        # 1 pays 40 but owes 10: is owed 30
        # 2 owes 10
        # 3 owes 20
        more_drinks = self._add_expense(night_out, 40)
        self._add_payment(more_drinks, partner_1, 40)

        self.assertEqual(night_out.total_amount, 0)

        totals = night_out.total_partner_split_ids
        total_partner_1 = totals.filtered_domain(
            [("partner_id", "=", self.partner_1.id)]
        )
        self.assertEqual(total_partner_1.amount, 37.5 - 50 + 30)
        total_partner_2 = totals.filtered_domain(
            [("partner_id", "=", self.partner_2.id)]
        )
        self.assertEqual(total_partner_2.amount, -12.5 - 50 - 10)
        total_partner_3 = totals.filtered_domain(
            [("partner_id", "=", self.partner_3.id)]
        )
        self.assertEqual(total_partner_3.amount, -25 + 100 - 20)

        # Propose payments
        self.assertFalse(night_out.partner_payment_ids)
        night_out.generate_payment_proposals()
        proposed_payments = night_out.partner_payment_ids
        self.assertEqual(len(proposed_payments), 2)
        payment_2_to_1 = proposed_payments[0]
        self.assertEqual(payment_2_to_1.from_partner_id, partner_2)
        self.assertEqual(payment_2_to_1.to_partner_id, partner_1)
        self.assertEqual(payment_2_to_1.amount, 17.5)
        payment_2_to_3 = proposed_payments[1]
        self.assertEqual(payment_2_to_3.from_partner_id, partner_2)
        self.assertEqual(payment_2_to_3.to_partner_id, partner_3)
        self.assertEqual(payment_2_to_3.amount, 55)

        # Execute payments
        for proposed_payment in proposed_payments:
            proposed_payment.generate_payment()
        self.assertFalse(proposed_payments.exists())

        # Everything is paid for
        self.assertFalse(sum(night_out.total_partner_split_ids.mapped("amount")))

    def test_house_expenses(self):
        """Simulate expenses in a household."""
        house = self.split_account

        partner_1 = self.partner_1
        partner_2 = self.partner_2
        partner_3 = self.partner_3

        default_lines = house.partner_split_weight_ids
        default_partner_1 = default_lines.filtered_domain(
            [("partner_id", "=", partner_1.id)]
        )
        self.assertEqual(default_partner_1.weight, 1)
        default_partner_2 = default_lines.filtered_domain(
            [("partner_id", "=", partner_2.id)]
        )
        self.assertEqual(default_partner_2.weight, 1)
        # Only 2 partners
        default_partner_3 = default_lines.filtered_domain(
            [("partner_id", "=", partner_3.id)]
        )
        default_partner_3.unlink()

        # Salaries
        # 1: +2000
        # 2: +1500
        salary = self._add_expense(house, 0)
        self._add_payment(salary, partner_1, 2000)
        self._add_payment(salary, partner_2, 1500)
        self._assign_only_to(salary)

        # Shared expense
        # 1: -400
        # 2: -400
        self._add_expense(house, 800)

        # Not shared expense
        # 1: -100
        # 2: 0
        expense_1 = self._add_expense(house, 100)
        self._assign_only_to(expense_1, partner_1)

        self.assertEqual(house.total_amount, 2000 + 1500 - 800 - 100)

        totals = house.total_partner_split_ids
        total_partner_1 = totals.filtered_domain(
            [("partner_id", "=", self.partner_1.id)]
        )
        self.assertEqual(total_partner_1.amount, 2000 - 400 - 100)
        total_partner_2 = totals.filtered_domain(
            [("partner_id", "=", self.partner_2.id)]
        )
        self.assertEqual(total_partner_2.amount, 1500 - 400)
