# Copyright 2019 Simone Rubino <daemo00@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.fields import Command, first

from odoo.addons.base.tests.common import BaseCommon

EVENT_NBR = 2
REGISTRATION_NBR = 2
TOURNAMENT_NBR = 3
TEAM_NBR = 4
COMPONENT_NBR = 5
COURT_NBR = 2


class TestCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event_model = cls.env["event.event"]
        cls.component_model = cls.env["event.registration"]
        cls.court_model = cls.env["event.tournament.court"]
        cls.match_model = cls.env["event.tournament.match"]
        cls.match_mode_model = cls.env["event.tournament.match.mode"]
        cls.team_model = cls.env["event.tournament.team"]
        cls.tournament_model = cls.env["event.tournament"]

        cls.events = cls.event_model.browse()
        cls.tournaments = cls.tournament_model.browse()
        cls.teams = cls.team_model.browse()
        cls.registrations = cls.component_model.browse()
        cls.components = cls.component_model.browse()
        cls.courts = cls.court_model.browse()

        for event_index in range(EVENT_NBR):
            event = cls.create_event(event_index)

            registrations = cls.create_registrations(event, event_index)
            cls.registrations |= registrations

            courts = cls.create_courts(event, event_index)
            cls.courts |= courts

            for tournament_index in range(TOURNAMENT_NBR):
                tournament = cls.create_tournament(
                    courts, event, event_index, tournament_index
                )
                cls.tournaments |= tournament
                for team_index in range(TEAM_NBR):
                    team = cls.create_team(
                        event, tournament, event_index, team_index, tournament_index
                    )
                    cls.teams |= team
                    cls.components |= team.component_ids

    @classmethod
    def component_values(
        cls, component_index, event, event_index, team_index, tournament_index
    ):
        return {
            "event_id": event.id,
            "name": f"event {event_index}, "
            f"tournament {tournament_index}, "
            f"team {team_index}, "
            f"component {component_index}",
        }

    @classmethod
    def create_team(
        cls,
        event,
        tournament,
        event_index=None,
        team_index=None,
        tournament_index=None,
    ):
        team = cls.team_model.create(
            {
                "tournament_id": tournament.id,
                "name": f"event {event_index}, "
                f"tournament {tournament_index}, "
                f"team {team_index}",
                "component_ids": [
                    (
                        0,
                        0,
                        cls.component_values(
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

    @classmethod
    def create_tournament(cls, courts, event, event_index, tournament_index):
        tournament = cls.tournament_model.create(
            {
                "event_id": event.id,
                "match_mode_id": cls.env.ref(
                    "event_tournament.event_tournament_match_mode_beach_volley"
                ).id,
                "court_ids": courts.ids,
                "name": f"event {event_index}, " f"tournament {tournament_index}",
            }
        )
        return tournament

    @classmethod
    def create_courts(cls, event, event_index):
        courts = cls.court_model.browse()
        for court_index in range(COURT_NBR):
            courts |= cls.court_model.create(
                {
                    "event_id": event.id,
                    "name": f"event {event_index}, " f"court {court_index}",
                }
            )
        return courts

    @classmethod
    def create_registrations(cls, event, event_index):
        registrations = cls.component_model.browse()
        for registration_index in range(REGISTRATION_NBR):
            registrations |= cls.component_model.create(
                {
                    "event_id": event.id,
                    "name": f"event {event_index}, " f"component {registration_index}",
                }
            )
        return registrations

    @classmethod
    def create_event(cls, event_index):
        event = cls.event_model.create(
            {
                "name": f"event {event_index}",
                "date_begin": date(2000, 1, 1),
                "date_end": date(2000, 1, 2),
            }
        )
        cls.events |= event
        return event

    @classmethod
    def get_match_1_2(cls, teams):
        tournament = first(cls.tournaments)
        court = first(cls.courts)
        tournament.update({"court_ids": court.ids})
        teams.update({"tournament_id": tournament.id})
        match_values = {
            "tournament_id": tournament.id,
            "court_id": court.id,
            "team_ids": teams.ids,
        }
        match_values.update(cls.get_match_lines_1_2(teams))
        match = cls.match_model.create(match_values)
        return match

    @classmethod
    def get_match_lines_1_2(cls, teams):
        # 10-21, 21-18, 8-15
        set_1_values = {
            "name": "test set 1",
            "result_ids": [
                Command.create(
                    {
                        "team_id": teams[0].id,
                        "score": 10,
                    }
                ),
                Command.create(
                    {
                        "team_id": teams[1].id,
                        "score": 21,
                    }
                ),
            ],
        }
        set_2_values = {
            "name": "test set 2",
            "result_ids": [
                Command.create(
                    {
                        "team_id": teams[0].id,
                        "score": 21,
                    }
                ),
                Command.create(
                    {
                        "team_id": teams[1].id,
                        "score": 18,
                    }
                ),
            ],
        }
        set_3_values = {
            "name": "test set 3",
            "result_ids": [
                Command.create(
                    {
                        "team_id": teams[0].id,
                        "score": 8,
                    }
                ),
                Command.create(
                    {
                        "team_id": teams[1].id,
                        "score": 15,
                    }
                ),
            ],
        }
        return {
            "set_ids": [
                Command.clear(),
                Command.create(set_1_values),
                Command.create(set_2_values),
                Command.create(set_3_values),
            ],
        }

    @classmethod
    def get_match_1_1(cls, teams):
        tournament = first(cls.tournaments)
        court = first(cls.courts)
        tournament.update({"court_ids": court.ids})
        teams.update({"tournament_id": tournament.id})
        match_values = {
            "tournament_id": tournament.id,
            "court_id": court.id,
            "team_ids": teams.ids,
        }
        match_values.update(cls.get_match_lines_1_1(teams))
        match = cls.match_model.create(match_values)
        return match

    @classmethod
    def get_match_lines_1_1(cls, teams):
        # 10-21, 21-18
        set_1_values = {
            "name": "1",
            "result_ids": [
                Command.create(
                    {
                        "team_id": teams[0].id,
                        "score": 10,
                    }
                ),
                Command.create(
                    {
                        "team_id": teams[1].id,
                        "score": 21,
                    }
                ),
            ],
        }
        set_2_values = {
            "name": "2",
            "result_ids": [
                Command.create(
                    {
                        "team_id": teams[0].id,
                        "score": 21,
                    }
                ),
                Command.create(
                    {
                        "team_id": teams[1].id,
                        "score": 18,
                    }
                ),
            ],
        }
        return {
            "set_ids": [
                Command.clear(),
                Command.create(set_1_values),
                Command.create(set_2_values),
            ],
        }

    @classmethod
    def get_match_2_0(cls, teams):
        tournament = first(cls.tournaments)
        court = first(cls.courts)
        tournament.update({"court_ids": court.ids})
        teams.update({"tournament_id": tournament.id})
        match_values = {
            "tournament_id": tournament.id,
            "court_id": court.id,
            "team_ids": teams.ids,
        }
        match_values.update(cls.get_match_lines_2_0(teams))
        match = cls.match_model.create(match_values)
        return match

    @classmethod
    def get_match_lines_2_0(cls, teams):
        # 21-10, 21-18
        set_1_values = {
            "name": "1",
            "result_ids": [
                Command.create(
                    {
                        "team_id": teams[0].id,
                        "score": 21,
                    }
                ),
                Command.create(
                    {
                        "team_id": teams[1].id,
                        "score": 10,
                    }
                ),
            ],
        }
        set_2_values = {
            "name": "2",
            "result_ids": [
                Command.create(
                    {
                        "team_id": teams[0].id,
                        "score": 21,
                    }
                ),
                Command.create(
                    {
                        "team_id": teams[1].id,
                        "score": 18,
                    }
                ),
            ],
        }
        return {
            "set_ids": [
                Command.clear(),
                Command.create(set_1_values),
                Command.create(set_2_values),
            ],
        }
