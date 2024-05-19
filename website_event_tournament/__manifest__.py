#  Copyright 2022 Simone Rubino
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Tournaments in website",
    "summary": "Manage tournaments in website",
    "version": "16.0.1.0.0",
    "category": "Website",
    "author": "Daemo00's developments",
    "website": "https://github.com/Daemo00/odoo-modules"
    "/tree/15.0/website_event_tournament",
    "license": "AGPL-3",
    "depends": [
        "website_event",
        "event_tournament",
    ],
    "data": [
        "security/ir.model.access.csv",
        "templates/event_registration_templates.xml",
        "templates/event_templates.xml",
        "views/event_tournament_view.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_event_tournament/static/src/js/registration.js",
        ],
    },
}
