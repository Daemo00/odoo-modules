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

        for key, value in form_details.items():
            if key.startswith("team_name"):
                input_name, registration_index, tournament_id = key.split("-")
                # Registration form is 1-based but list is 0-based
                registration_index = int(registration_index) - 1

                if input_name != "team_name":
                    # Skip any false positive
                    continue

                team_name = value.strip()
                if not team_name:
                    continue

                # Teams have to be created
                # when there are the components
                # because a team without components is not valid.
                # Just save them for later use,
                # see _create_attendees_from_registration_post.
                registration_values = registrations_values[registration_index]
                registration_values.setdefault("tournament_team_ids", list()).append(
                    (tournament_id, team_name)
                )

        return registrations_values

    def _create_attendees_from_registration_post(self, event, registration_data):
        attendees_teams = dict()
        for registration_index, registration_values in enumerate(registration_data):
            if "tournament_team_ids" in registration_values:
                attendees_teams[registration_index] = registration_values.pop(
                    "tournament_team_ids"
                )

        attendees = super()._create_attendees_from_registration_post(
            event, registration_data
        )

        # {
        #     tournament (model):
        #     {
        #         team (name): component (model),
        #     },
        # }
        tournament_to_team_to_components = dict()

        tournament_model = request.env["event.tournament"]
        for attendee_index, attendee in enumerate(attendees):
            attendee_teams = attendees_teams[attendee_index]
            for tournament_id, team_name in attendee_teams:
                tournament = tournament_model.browse(int(tournament_id))
                if tournament not in tournament_to_team_to_components:
                    tournament_to_team_to_components[tournament] = dict()

                team_dict = tournament_to_team_to_components[tournament]
                if team_name not in team_dict:
                    team_dict[team_name] = attendee.browse()
                team_dict[team_name] |= attendee

        # Create or update the teams
        for tournament, team_dict in tournament_to_team_to_components.items():
            tournament_teams = tournament.team_ids
            for team_name, components in team_dict.items():
                tournament_team = tournament_teams.filtered_domain(
                    [("name", "=", team_name)]
                )
                tournament_team = first(tournament_team)
                # Sudo is needed to manipulate teams
                # because their validation must
                # check with other attendees of the event
                # that is normally forbidden to portal users
                if not tournament_team:
                    # Team does not exist, create it
                    tournament_team.sudo().create(
                        {
                            "tournament_id": tournament.id,
                            "name": team_name,
                            "component_ids": components,
                        }
                    )
                else:
                    tournament_team.sudo().component_ids |= components

        return attendees
