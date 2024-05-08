#  Copyright 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import csv
from datetime import datetime

from odoo import fields, models


class ImportConti(models.TransientModel):
    _name = "account_partner_split.import_conti"
    _description = "Import Conti"

    file_name = fields.Char()
    file_data = fields.Binary(
        required=True,
    )
    thousand_sep = fields.Char(
        required=True,
        default=".",
    )
    cents_sep = fields.Char(
        required=True,
        default=",",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        required=True,
        default=lambda model: model.env.company.currency_id,
    )

    def import_file(self):
        self.ensure_one()
        account_id = self.env.context.get("active_id")
        account_model = self.env.context.get("active_model")
        account = self.env[account_model].browse(account_id)

        thousand_sep = self.thousand_sep
        cents_sep = self.cents_sep
        currency_symbol = self.currency_id.symbol

        content = base64.decodebytes(self.file_data).decode()
        csv_lines = content.splitlines()
        csv_dicts = list(csv.DictReader(csv_lines))
        partner_cache = {}

        for csv_dict in csv_dicts:
            amount = csv_dict.get(" Importo EUR")
            amount = (
                amount.replace(thousand_sep, "")
                .replace(cents_sep, ".")
                .replace(currency_symbol, "")
            )
            if not amount:
                break
            amount = float(amount)

            split_dict = {
                "account_id": account.id,
                "name": csv_dict.get("Descrizione operazione"),
                "date": datetime.strptime(csv_dict.get("Data valuta"), "%d/%m/%Y")
                if csv_dict.get("Data valuta")
                else False,
            }

            line = self.env["account_partner_split.account.line"].create(split_dict)

            partner_name = csv_dict.get("Partner")
            if not partner_name:
                partner_to_paid_amount = line.split_by_weight(amount)
            else:
                partner = partner_cache.get(partner_name)
                if not partner:
                    partner = self.env["res.partner"].search(
                        [
                            ("name", "=", partner_name),
                        ],
                        limit=1,
                    )
                    partner_cache[partner_name] = partner
                partner_to_paid_amount = {
                    partner: amount,
                }

            line.partner_line_ids = line.partner_line_ids._get_update_commands(
                partner_to_paid_amount,
            )
