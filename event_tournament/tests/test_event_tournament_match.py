#  Copyright 2019 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError

from .test_common import TestCommon


class TestEventTournamentMatch(TestCommon):
    def test_get_sets_info(self):
        """
        Create a match,
        check that sets info are correctly computed.
        """
        teams = self.teams[:2]
        match = self.get_match_1_2(teams)
        self.assertDictEqual(
            {teams[0]: (2, 1, 39, 54), teams[1]: (1, 2, 54, 39)}, match.get_sets_info()
        )

    def test_action_done(self):
        """
        Create a match,
        check that the winner is correctly computed.
        """
        teams = self.teams[:2]
        match = self.get_match_1_2(teams)
        match.action_done()
        self.assertTrue(match.winner_team_id == teams[1])
        with self.assertRaises(UserError) as ue:
            match.action_done()
        self.assertIn(match.display_name, ue.exception.args[0])

    def test_action_done_tie(self):
        """
        Create a match,
        check that ties produce no winner.
        """
        teams = self.teams[:2]
        match = self.get_match_1_1(teams)
        match.action_done()
        self.assertFalse(match.winner_team_id)
