#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.fields import first
from .test_common import TestCommon


class TestEventTournamentTeam(TestCommon):

    def test_onchange_tournament(self):
        """
        Change the tournament,
        check that domain of components and matches is modified.
        """
        team = first(self.teams)
        onchange_values = team.onchange_tournament()
        self.assertIn('domain', onchange_values)
        self.assertIn('component_ids', onchange_values['domain'])
        self.assertIn('match_ids', onchange_values['domain'])

    def test_constrain_components_event(self):
        component_0 = first(self.events[0].registration_ids)
        component_1 = first(self.events[1].registration_ids)
        self.assertTrue(component_0)
        self.assertTrue(component_1)
        team_name = 'test constrain components'
        with self.assertRaises(ValidationError) as ve:
            self.team_model.create({
                'name': team_name,
                'tournament_id': first(self.tournaments).id,
                'component_ids': [(4, component_0.id), (4, component_1.id)]
            })
        self.assertIn(team_name, str(ve.exception))
