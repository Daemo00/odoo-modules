#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import first
from odoo.tests import TransactionCase, date

COURT_NBR = 2
TEAM_NBR = 3
TOURNAMENT_NBR = 2


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

        self.event = self.event_model.create({
            'name': 'test event',
            'date_begin': date(2000, 1, 1),
            'date_end': date(2000, 1, 2),
        })

        self.tournaments = self.tournament_model.create([{
            'event_id': self.event.id,
            'name': 'test tournament {tournament_index}'.format(
                tournament_index=tournament_index),
        } for tournament_index in range(TOURNAMENT_NBR)])

        self.teams = self.team_model.create([{
            # Try this with tournaments[0] to reproduce
            # https://github.com/odoo/odoo/pull/39295
            'tournament_id': self.tournaments[1].id,
            'name': 'test team {team_index}'
                .format(team_index=team_index),
        } for team_index in range(TEAM_NBR)])

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
