#  Copyright 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import os

from odoo.modules import get_resource_path

from odoo.addons.account_partner_split.tests.common import TestCommon


class TestImportConti(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard_model = cls.env["account_partner_split.import_conti"]

    def get_wizard_for_file(self, account, file_name):
        resp_path = get_resource_path(self.test_module, "tests", "data", file_name)
        with open(resp_path, "rb") as resp_file:
            wizard = self.wizard_model.with_context(
                active_model=account._name,
                active_id=account.id,
            ).create(
                {
                    "file_data": base64.encodebytes(resp_file.read()),
                    "file_name": os.path.basename(resp_file.name),
                }
            )
        return wizard

    def test_import(self):
        conti = self.split_account

        partner_1 = self.partner_1
        partner_1.name = "Partner 1"
        partner_2 = self.partner_2
        partner_2.name = "Partner 2"
        partner_3 = self.partner_3

        default_lines = conti.partner_split_weight_ids
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

        wizard = self.get_wizard_for_file(conti, "conti.csv")
        wizard.import_file()

        self.assertEqual(conti.total_amount, 7000)

        totals = conti.total_partner_split_ids
        total_partner_1 = totals.filtered_domain(
            [("partner_id", "=", self.partner_1.id)]
        )
        self.assertEqual(total_partner_1.amount, 2500)
        total_partner_2 = totals.filtered_domain(
            [("partner_id", "=", self.partner_2.id)]
        )
        self.assertEqual(total_partner_2.amount, 4500)
