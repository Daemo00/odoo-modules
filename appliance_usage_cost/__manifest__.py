#  Copyright 2024 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Appliance Usage Cost",
    "version": "17.0.1.0.0",
    "summary": "Calculate appliance usage costs based on utility contracts.",
    "license": "AGPL-3",
    "author": "Simone Rubino",
    "website": "https://github.com/Daemo00/odoo-modules",
    "depends": [
        "base",
        "uom",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/uom_data.xml",
        "data/utility_data.xml",
        "views/root_menus.xml",
        "views/appliance_views.xml",
        "views/program_views.xml",
        "views/usage_cycle_views.xml",
        "views/utility_contract_views.xml",
    ],
    "demo": [
        "demo/appliance_demo.xml",
        "demo/utility_contract_demo.xml",
    ],
}
