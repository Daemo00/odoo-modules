#  Copyright 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import csv
from io import StringIO

from odoo import fields, models
from odoo.tools import format_date


class ExportCSV(models.TransientModel):
    _name = "account_partner_split.export_csv"
    _description = "Export CSV"

    file_name = fields.Char(readonly=True)
    file_data = fields.Binary(readonly=True)
    state = fields.Selection(
        selection=[
            ("confirm", "Confirm"),
            ("download", "Download"),
        ],
        default="confirm",
    )

    def export(self):
        self.ensure_one()
        account_id = self.env.context.get("active_id")
        account_model = self.env.context.get("active_model")
        account = self.env[account_model].browse(account_id)

        headers = [
            "Accounting Date",
            "Invoice Date",
            "Description",
            "Category",
            "Amount",
            "Partner",
        ]

        csv_lines = []
        for line in account.line_ids:
            csv_line = {
                "Accounting Date": format_date(self.env, line.accounting_date),
                "Invoice Date": format_date(self.env, line.invoice_date),
                "Description": line.name or "",
                "Category": ", ".join(line.tag_ids.mapped("name")),
            }
            totals = line.total_partner_split_ids
            for total in totals:
                total_csv_line = csv_line.copy()
                total_csv_line.update(
                    {"Amount": total.amount, "Partner": total.partner_id.display_name}
                )
                csv_lines.append(total_csv_line)

        out = StringIO()
        writer = csv.DictWriter(out, headers)
        writer.writeheader()
        writer.writerows(csv_lines)
        self.file_data = base64.b64encode(out.getvalue().encode())
        self.file_name = "out.csv"
        self.state = "download"

        wiz_action = self.env["ir.actions.act_window"]._for_xml_id(
            "account_partner_split.export_csv_action"
        )
        wiz_action["res_id"] = self.id
        return wiz_action
