#  Copyright 2020 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Event tournament",
    "summary": "Implement tournaments in Odoo events",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Simone Rubino",
    "depends": ["event", "partner_contact_birthdate", "partner_contact_gender"],
    "data": [
        "security/ir.model.access.csv",
        "data/event_tournament_match_mode_data.xml",
        "views/event_event_view.xml",
        "views/event_registration_view.xml",
        "views/event_tournament_view.xml",
        "views/event_tournament_court_view.xml",
        "views/event_tournament_match_view.xml",
        "views/event_tournament_mode_view.xml",
        "views/event_tournament_team_view.xml",
        "views/report_matches_schedule.xml",
        "wizards/import_csv_bv4w_views.xml",
    ],
}
