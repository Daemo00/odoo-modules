#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Split Expenses among Partners",
    "summary": "Generate moves splitting costs among partners",
    "category": "Accounting/Accounting",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Simone Rubino",
    "website": "https://github.com/Daemo00/odoo-modules/tree/16.0/event_tournament",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/export_csv_views.xml",
        "wizards/import_conti_views.xml",
        "views/root_menus.xml",
        "views/partner_pay_split_views.xml",
        "views/partner_payment_views.xml",
        "views/partner_split_views.xml",
        "views/partner_total_split_views.xml",
        "views/split_account_line_views.xml",
        "views/split_account_views.xml",
    ],
}
