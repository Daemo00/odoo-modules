#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, date


class TestCommon (TransactionCase):

    def setUp(self):
        super().setUp()
        self.event_model = self.env['event.event']
        self.component_model = self.env['event.registration']
        self.team_model = self.env['event.tournament.team']
        self.tournament_model = self.env['event.tournament']

        self.event = self.event_model.create({
            'name': 'test event',
            'date_begin': date(2000, 1, 1),
            'date_end': date(2000, 1, 2),
        })
        self.tournament_1 = self.tournament_model.create({
            'name': 'test tournament 1',
            'event_id': self.event.id,
        })
        self.tournament_2 = self.tournament_model.create({
            'name': 'test tournament 2',
            'event_id': self.event.id,
        })
