#  Copyright 2019 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import first
from odoo.tests import TransactionCase, date

EVENT_NBR = 2
REGISTRATION_NBR = 2
TOURNAMENT_NBR = 3
TEAM_NBR = 4
COMPONENT_NBR = 5
COURT_NBR = 2


class TestCommon(TransactionCase):
    def setUp(self):
        super().setUp()
        self.event_model = self.env["event.event"]
        self.component_model = self.env["event.registration"]
        self.court_model = self.env["event.tournament.court"]
        self.match_model = self.env["event.tournament.match"]
        self.match_mode_model = self.env["event.tournament.match.mode"]
        self.team_model = self.env["event.tournament.team"]
        self.tournament_model = self.env["event.tournament"]

        self.events = self.event_model.browse()
        self.tournaments = self.tournament_model.browse()
        self.teams = self.team_model.browse()
        self.registrations = self.component_model.browse()
        self.components = self.component_model.browse()
        self.courts = self.court_model.browse()

        for event_index in range(EVENT_NBR):
            event = self.create_event(event_index)

            registrations = self.create_registrations(event, event_index)
            self.registrations |= registrations

            courts = self.create_courts(event, event_index)
            self.courts |= courts

            for tournament_index in range(TOURNAMENT_NBR):
                tournament = self.create_tournament(
                    courts, event, event_index, tournament_index
                )
                self.tournaments |= tournament
                for team_index in range(TEAM_NBR):
                    team = self.create_team(
                        event, tournament, event_index, team_index, tournament_index
                    )
                    self.teams |= team
                    self.components |= team.component_ids

    def component_values(
        self, component_index, event, event_index, team_index, tournament_index
    ):
        return {
            "event_id": event.id,
            "name": "event {event_index}, "
            "tournament {tournament_index}, "
            "team {team_index}, "
            "component {component_index}".format(
                event_index=event_index,
                tournament_index=tournament_index,
                team_index=team_index,
                component_index=component_index,
            ),
        }

    def create_team(
        self,
        event,
        tournament,
        event_index=None,
        team_index=None,
        tournament_index=None,
    ):
        team = self.team_model.create(
            {
                "tournament_id": tournament.id,
                "name": "event {event_index}, "
                "tournament {tournament_index}, "
                "team {team_index}".format(
                    event_index=event_index,
                    tournament_index=tournament_index,
                    team_index=team_index,
                ),
                "component_ids": [
                    (
                        0,
                        0,
                        self.component_values(
                            component_index,
                            event,
                            event_index,
                            team_index,
                            tournament_index,
                        ),
                    )
                    for component_index in range(COMPONENT_NBR)
                ],
            }
        )
        return team

    def create_tournament(self, courts, event, event_index, tournament_index):
        tournament = self.tournament_model.create(
            {
                "event_id": event.id,
                "court_ids": courts.ids,
                "name": "event {event_index}, "
                "tournament {tournament_index}".format(
                    event_index=event_index, tournament_index=tournament_index
                ),
            }
        )
        return tournament

    def create_courts(self, event, event_index):
        courts = self.court_model.browse()
        for court_index in range(COURT_NBR):
            courts |= self.court_model.create(
                {
                    "event_id": event.id,
                    "name": "event {event_index}, "
                    "court {court_index}".format(
                        event_index=event_index, court_index=court_index
                    ),
                }
            )
        return courts

    def create_registrations(self, event, event_index):
        registrations = self.component_model.browse()
        for registration_index in range(REGISTRATION_NBR):
            registrations |= self.component_model.create(
                {
                    "event_id": event.id,
                    "name": "event {event_index}, "
                    "component {registration_index}".format(
                        event_index=event_index, registration_index=registration_index
                    ),
                }
            )
        return registrations

    def create_event(self, event_index):
        event = self.event_model.create(
            {
                "name": "event {event_index}".format(event_index=event_index),
                "date_begin": date(2000, 1, 1),
                "date_end": date(2000, 1, 2),
            }
        )
        self.events |= event
        return event

    def get_match_1_2(self, teams):
        tournament = first(self.tournaments)
        court = first(self.courts)
        tournament.update({"court_ids": court.ids})
        teams.update({"tournament_id": tournament.id})
        match_values = {
            "tournament_id": tournament.id,
            "court_id": court.id,
            "team_ids": teams.ids,
        }
        match_values.update(self.get_match_lines_1_2(teams))
        match = self.match_model.create(match_values)
        return match

    def get_match_lines_1_2(self, teams):
        line_1_values = {
            "team_id": teams[0].id,
            "set_1": 10,
            "set_3": 21,
            "set_4": 8,
        }
        line_2_values = {
            "team_id": teams[1].id,
            "set_1": 21,
            "set_3": 18,
            "set_4": 15,
        }
        return {
            "line_ids": [(0, 0, line_1_values), (0, 0, line_2_values)],
        }

    def get_match_1_1(self, teams):
        tournament = first(self.tournaments)
        court = first(self.courts)
        tournament.update({"court_ids": court.ids})
        teams.update({"tournament_id": tournament.id})
        match_values = {
            "tournament_id": tournament.id,
            "court_id": court.id,
            "team_ids": teams.ids,
        }
        match_values.update(self.get_match_lines_1_1(teams))
        match = self.match_model.create(match_values)
        return match

    def get_match_lines_1_1(self, teams):
        return {
            "line_ids": [
                (0, 0, {"team_id": teams[0].id, "set_1": 10, "set_3": 21}),
                (0, 0, {"team_id": teams[1].id, "set_1": 21, "set_3": 18}),
            ],
        }
