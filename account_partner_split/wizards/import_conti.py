#  Copyright 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import csv
from datetime import datetime

from odoo import Command, fields, models


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

    def import_file(self):
        self.ensure_one()
        account_id = self.env.context.get("active_id")
        account_model = self.env.context.get("active_model")
        account = self.env[account_model].browse(account_id)

        thousand_sep = self.thousand_sep
        cents_sep = self.cents_sep

        content = base64.decodebytes(self.file_data).decode()
        csv_lines = content.splitlines()
        csv_dicts = list(csv.DictReader(csv_lines))
        partner_cache = {}

        for csv_dict in csv_dicts:
            split_dict = {
                "split_account_id": account.id,
                "name": csv_dict.get("Descrizione operazione"),
                "accounting_date": datetime.strptime(
                    csv_dict.get("Data operazione"), "%d/%m/%Y"
                )
                if csv_dict.get("Data operazione")
                else False,
                "invoice_date": datetime.strptime(
                    csv_dict.get("Data valuta"), "%d/%m/%Y"
                )
                if csv_dict.get("Data valuta")
                else False,
            }

            tag_names = csv_dict.get("Tipologia")
            if tag_names:
                tag_names = tag_names.split(",")
                tags = self.env["account_partner_split.account.line.tag"].browse()
                for tag_name in tag_names:
                    tag = self.env["account_partner_split.account.line.tag"].search(
                        [("name", "=", tag_name)]
                    )
                    if not tag:
                        tag = self.env["account_partner_split.account.line.tag"].create(
                            {
                                "name": tag_name,
                            }
                        )
                    tags |= tag
                split_dict["tag_ids"] = [Command.set(tags.ids)]

            line = self.env["account_partner_split.account.line"].create(split_dict)

            amount = csv_dict.get(" Importo EUR")
            amount = amount.replace(thousand_sep, "").replace(cents_sep, ".")
            amount = float(amount)

            partner_name = csv_dict.get("Partner")
            if not partner_name:
                line.to_pay_amount = -amount
                line.onchange_split_account_id()
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
                line.paying_partner_split_ids = [
                    Command.create(
                        {
                            "partner_id": partner.id,
                            "amount": amount,
                        }
                    )
                ]
                line.partner_split_weight_ids = [
                    Command.clear(),
                ]
