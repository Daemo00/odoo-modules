#  Copyright 2020 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Event tournament",
    "summary": "Implement tournaments in Odoo events",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Simone Rubino",
    "website": "https://github.com/Daemo00/odoo-modules/tree/16.0/event_tournament",
    "depends": [
        "event",
        "partner_contact_birthdate",
        "partner_contact_gender",
        "web_timeline",
        "web_widget_x2many_2d_matrix",
        "web_m2x_options",
    ],
    "external_dependencies": {
        "python": [
            "more_itertools",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/event_tournament_match_mode_data.xml",
        "templates/report_check_in.xml",
        "templates/report_matches_schedule.xml",
        "templates/report_matches_schedule_component.xml",
        "templates/report_matches_schedule_team.xml",
        "templates/report_matches_schedule_tournament.xml",
        "views/root_menus.xml",
        "views/event_event_view.xml",
        "views/event_registration_view.xml",
        "views/event_tournament_view.xml",
        "views/event_tournament_court_view.xml",
        "views/event_tournament_match_view.xml",
        "views/event_tournament_mode_view.xml",
        "views/event_tournament_team_view.xml",
        "wizards/import_csv_bv4w_views.xml",
    ],
}
