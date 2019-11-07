#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import first
from odoo.tests import TransactionCase, date

EVENT_NBR = 2
TOURNAMENT_NBR = 2
TEAM_NBR = 3
COMPONENT_NBR = 2
COURT_NBR = 2


class TestCommon (TransactionCase):

    def setUp(self):
        super().setUp()
        self.event_model = self.env['event.event']
        self.component_model = self.env['event.registration']
        self.court_model = self.env['event.tournament.court']
        self.match_model = self.env['event.tournament.match']
        self.match_mode_model = self.env['event.tournament.match.mode']
        self.team_model = self.env['event.tournament.team']
        self.tournament_model = self.env['event.tournament']

        self.events = self.event_model.browse()
        self.tournaments = self.tournament_model.browse()
        self.teams = self.team_model.browse()
        self.components = self.component_model.browse()

        for event_index in range(EVENT_NBR):
            event = self.event_model.create({
                'name': 'event {event_index}'.format(
                    event_index=event_index),
                'date_begin': date(2000, 1, 1),
                'date_end': date(2000, 1, 2),
            })
            self.events |= event

            for component_index in range(COMPONENT_NBR):
                self.components |= self.component_model.create({
                    'event_id': event.id,
                    'name': 'event {event_index}, '
                            'component {component_index}'.format(
                        event_index=event_index,
                        component_index=component_index),
                })
            for tournament_index in range(TOURNAMENT_NBR):
                tournament = self.tournament_model.create({
                    'event_id': event.id,
                    'name': 'event {event_index}, '
                            'tournament {tournament_index}'.format(
                        event_index=event_index,
                        tournament_index=tournament_index),
                })
                self.tournaments |= tournament
                for team_index in range(TEAM_NBR):
                    team = self.team_model.create({
                        'tournament_id': tournament.id,
                        'name': 'event {event_index}, '
                                'tournament {tournament_index},'
                                'team {team_index}'.format(
                            event_index=event_index,
                            tournament_index=tournament_index,
                            team_index=team_index)
                    })
                    self.teams |= team

        self.courts = self.court_model.create([{
            'name': 'test court {court_index}'
                .format(court_index=court_index),
        } for court_index in range(COURT_NBR)])

    def get_match_2_1(self, teams):
        tournament = first(self.tournaments)
        court = first(self.courts)
        tournament.update({'court_ids': court.ids})
        teams.update({'tournament_id': tournament.id})
        match = self.match_model.create({
            'tournament_id': tournament.id,
            'court_id': court.id,
            'team_ids': teams.ids,
            'line_ids': [
                (0, 0, {
                    'team_id': teams[0].id,
                    'set_1': 10,
                    'set_3': 21,
                    'set_4': 8,
                }),
                (0, 0, {
                    'team_id': teams[1].id,
                    'set_1': 21,
                    'set_3': 18,
                    'set_4': 15,
                }),
            ]
        })
        return match

    def get_match_1_1(self, teams):
        tournament = first(self.tournaments)
        court = first(self.courts)
        tournament.update({'court_ids': court.ids})
        teams.update({'tournament_id': tournament.id})
        match = self.match_model.create({
            'tournament_id': tournament.id,
            'court_id': court.id,
            'team_ids': teams.ids,
            'line_ids': [
                (0, 0, {
                    'team_id': teams[0].id,
                    'set_1': 10,
                    'set_3': 21,
                }),
                (0, 0, {
                    'team_id': teams[1].id,
                    'set_1': 21,
                    'set_3': 18,
                }),
            ]
        })
        return match
