#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .test_common import TestCommon


class TestEventRegistration(TestCommon):

    def setUp(self):
        super().setUp()
        self.component = self.component_model.create({
            'event_id': self.event.id,
        })

    def test_onchange_partner(self):
        """
        Assign a partner to the component,
        check that the gender is propagated from the partner to the component.
        """
        partner = self.env['res.partner'].create({
            'name': 'test partner',
            'gender': 'male',
        })
        self.assertFalse(self.component.gender)
        self.component._onchange_partner()
        self.assertFalse(self.component.gender)
        self.component.partner_id = partner
        self.component._onchange_partner()
        self.assertEqual(self.component.gender, partner.gender)

    def test_compute_tournaments(self):
        """
        Assign a team to the component,
        check that the component is in the team's tournament.
        """
        self.assertFalse(self.component.tournament_team_ids)
        team = self.team_model.create({
            'event_id': self.event.id,
            'tournament_id': self.tournament_1.id,
            'name': 'test team',
            'component_ids': [(4, self.component.id)]
        })
        self.assertIn(team, self.component.tournament_team_ids)
        self.component.compute_tournaments()
        self.assertIn(self.component, team.tournament_id.component_ids)
