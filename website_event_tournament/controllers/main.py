#  Copyright 2022 Simone Rubino
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo.fields import first
from odoo.http import request

from odoo.addons.website_event.controllers.main import WebsiteEventController


class WebsiteEventTournamentController(WebsiteEventController):
    def get_team_names(self, value):
        # Extract quoted teams
        pattern = re.compile(r"\"([^\"]*)\"")
        quoted_teams = pattern.findall(value)

        # Extract unquoted teams
        unquoted_teams_str = pattern.sub("", value)  # Remove quoted teams
        unquoted_teams_list = unquoted_teams_str.split(",")
        unquoted_teams_list = map(
            str.strip, unquoted_teams_list
        )  # Remove spaces from teams names
        unquoted_teams_list = filter(None, unquoted_teams_list)  # Purge empty names
        unquoted_teams_list = list(unquoted_teams_list)

        teams_names = quoted_teams + unquoted_teams_list
        return teams_names

    def _process_attendees_form(self, event, form_details):
        """
        Process data posted from the attendee details form.

        There will be fields formatted like team_names-#{counter}-#{tournament.id}.
        """
        registrations_values = super()._process_attendees_form(event, form_details)

        tournament_model = request.env["event.tournament"]
        for key, value in form_details.items():
            if key.startswith("team_names"):
                input_name, registration_index, tournament_id = key.split("-")
                # Registration form is 1-based but list is 0-based
                registration_index = int(registration_index) - 1
                registration_values = registrations_values[registration_index]
                tournament = tournament_model.browse(int(tournament_id))
                registration_values.setdefault("tournament_ids", list()).append(
                    (4, tournament.id)
                )
                if input_name == "team_names":
                    tournament_teams = tournament.team_ids
                    teams_names = self.get_team_names(value)
                    for team_name in teams_names:
                        tournament_team = tournament_teams.filtered_domain(
                            [("name", "=", team_name)]
                        )
                        tournament_team = first(tournament_team)
                        if not tournament_team:
                            # Team does not exist, create it
                            tournament_team = tournament_team.create(
                                {
                                    "tournament_id": tournament.id,
                                    "name": team_name,
                                }
                            )
                        registration_values.setdefault(
                            "tournament_team_ids", list()
                        ).append((4, tournament_team.id))

        return registrations_values
