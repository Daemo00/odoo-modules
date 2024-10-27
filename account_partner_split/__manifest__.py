#  Copyright 2022 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Split Expenses among Partners",
    "summary": "Generate moves splitting costs among partners",
    "category": "Accounting/Accounting",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Simone Rubino",
    "website": "https://github.com/Daemo00/odoo-modules",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/export_csv_views.xml",
        "wizards/import_conti_views.xml",
        "views/root_menus.xml",
        "views/account_line_views.xml",
        "views/account_views.xml",
        "views/partner_amount_views.xml",
        "views/partner_payment_views.xml",
        "views/partner_weight_views.xml",
    ],
}
