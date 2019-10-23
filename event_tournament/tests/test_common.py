#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, date


class TestCommon (TransactionCase):

    def setUp(self):
        super().setUp()
        self.event_model = self.env['event.event']
        self.component_model = self.env['event.registration']
        self.court_model = self.env['event.tournament.court']
        self.match_model = self.env['event.tournament.match']
        self.team_model = self.env['event.tournament.team']
        self.tournament_model = self.env['event.tournament']

        self.court = self.court_model.create({
            'name': 'test court',
        })
        self.event = self.event_model.create({
            'name': 'test event',
            'date_begin': date(2000, 1, 1),
            'date_end': date(2000, 1, 2),
            'court_ids': self.court.ids
        })
        self.tournaments = self.tournament_model.create([{
            'event_id': self.event.id,
            'name': 'test tournament {tourn_index}'.format(
                tourn_index=tourn_index),
        } for tourn_index in range(2)])
        for tournament in self.tournaments:
            self.teams = self.team_model.create([{
                'tournament_id': tournament.id,
                'name': 'test team {team_index}'.format(team_index=team_index),
            }
                for team_index in range(1)])
