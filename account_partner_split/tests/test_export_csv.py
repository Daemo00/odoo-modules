#  Copyright 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from pathlib import Path

from odoo import fields
from odoo.modules import get_resource_path

from odoo.addons.account_partner_split.tests.common import TestCommon


class TestImportCSV(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard_model = cls.env["account_partner_split.export_csv"]

    def get_wizard(self, account):
        wizard = self.wizard_model.with_context(
            active_model=account._name,
            active_id=account.id,
        ).create({})
        return wizard

    def get_exported_file(self, account):
        wizard = self.get_wizard(account)
        wizard.export()
        file_data_base64 = wizard.file_data
        file_data = base64.b64decode(file_data_base64)
        return file_data

    def test_export_csv(self):
        """Export an account."""
        # Arrange
        account = self.split_account
        partner = self.partner_1
        tags = self.env["account_partner_split.account.line.tag"].create(
            [
                {
                    "name": "Tag 1",
                },
                {
                    "name": "Tag 2",
                },
            ]
        )

        expense = self._add_expense(account, 50)
        expense.name = "Shared"
        expense.invoice_date = fields.Datetime.to_datetime("2020-01-01 01:02:03")
        expense.accounting_date = fields.Datetime.to_datetime("2020-10-10 04:05:06")
        expense.tag_ids = tags

        partner_expense = self._add_expense(account, 100)
        partner_expense.invoice_date = False
        self._add_payment(partner_expense, partner, 100)

        # Act
        file_data = self.get_exported_file(account)

        # Assert
        expected_path = get_resource_path(
            self.test_module, "tests", "data", "export.csv"
        )
        expected = Path(expected_path).read_bytes()
        # Compare lines because created CSV has /r/n line separators,
        # but they cannot be saved in git
        self.assertCountEqual(
            file_data.splitlines(),
            expected.splitlines(),
        )
