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
        """
        Create a team,
        check that components of a team are from the same event.
        """
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

    def test_constrain_max_components_tournament(self):
        """
        Create a team,
        check that components of a team cannot be
        more than max components set on its tournament.
        """
        tournament = first(self.tournaments)
        team = first(tournament.team_ids)
        tournament.max_components = len(team.component_ids) - 1
        with self.assertRaises(ValidationError) as ve:
            tournament.action_check_rules()

        self.assertIn(team.name, str(ve.exception))
        self.assertIn(tournament.name, str(ve.exception))

    def test_constrain_min_components_tournament(self):
        """
        Create a team,
        check that components of a team cannot be
        less than min components set on its tournament.
        """
        tournament = first(self.tournaments)
        team = first(tournament.team_ids)
        tournament.min_components = len(team.component_ids) + 1
        with self.assertRaises(ValidationError) as ve:
            tournament.action_check_rules()

        self.assertIn(team.name, str(ve.exception))
        self.assertIn(tournament.name, str(ve.exception))

    def test_constrain_min_components_female_tournament(self):
        """
        Create a team,
        check that female components of a team cannot be
        less than min components set on its tournament.
        """
        tournament = first(self.tournaments)
        team = first(tournament.team_ids)
        tournament.min_components_female = len(team.component_ids) - 1

        # Generic gender check on teams
        with self.assertRaises(ValidationError) as ve:
            tournament.action_check_rules()

        tournament.component_ids.update({'gender': 'female'})
        # Female check on teams succeeds
        tournament.action_check_rules()

        tournament.min_components_female = len(team.component_ids) + 1

        # Female check on teams now fails
        with self.assertRaises(ValidationError) as ve:
            tournament.action_check_rules()

        self.assertIn(team.name, str(ve.exception))
        self.assertIn(tournament.name, str(ve.exception))

    def test_constrain_min_components_male_tournament(self):
        """
        Create a team,
        check that male components of a team cannot be
        less than min components set on its tournament.
        """
        tournament = first(self.tournaments)
        team = first(tournament.team_ids)
        tournament.min_components_male = len(team.component_ids) - 1

        # Generic gender check on teams
        with self.assertRaises(ValidationError) as ve:
            tournament.action_check_rules()

        tournament.component_ids.update({'gender': 'male'})
        # Male check on teams succeeds
        tournament.action_check_rules()

        tournament.min_components_male = len(team.component_ids) + 1

        # Male check on teams now fails
        with self.assertRaises(ValidationError) as ve:
            tournament.action_check_rules()

        self.assertIn(team.name, str(ve.exception))
        self.assertIn(tournament.name, str(ve.exception))

    def test_compute_matches_points(self):
        """
        End a match,
        check that points are correctly computed.
        """
        teams = self.teams[:2]
        match = self.get_match_1_2(teams)
        match.match_mode_id = self.ref(
            'event_tournament.event_tournament_match_mode_beach_volley')
        winner = teams[1]
        self.assertEqual(winner.sets_won, 0)
        self.assertEqual(winner.points_ratio, 0)
        self.assertEqual(winner.matches_points, 0)
        match.action_done()
        self.assertEqual(winner.sets_won, 2)
        self.assertEqual(winner.matches_points, 2)
        self.assertEqual(winner.points_ratio,
                         winner.points_done / winner.points_taken)

    def test_action_view_matches(self):
        """
        Create a team,
        check that `action_view_matches` creates an action
        that shows its matches.
        """
        team = self.teams[:1]
        action = team.action_view_matches()
        action_model = action.get('res_model')
        action_domain = action.get('domain')
        action_matches = self.env[action_model].search(action_domain)
        self.assertEqual(team.match_ids, action_matches)
