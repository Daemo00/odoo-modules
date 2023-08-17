#  Copyright 2019 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError

from .test_common import TestCommon


class TestEventTournamentMatchMode(TestCommon):
    def test_get_points(self):
        """
        Create a match,
        check that points are computed correctly with beach volley mode.
        """
        teams = self.teams[:2]
        match = self.get_match_1_2(teams)
        bv_mode = self.env.ref(
            "event_tournament." "event_tournament_match_mode_beach_volley"
        )
        match.action_done()
        self.assertDictEqual({teams[0]: 1, teams[1]: 2}, bv_mode.get_points(match))

    def test_get_points_error(self):
        """
        Create a match,
        check that an exception is raised if the result is not present
        in match's mode.
        """
        teams = self.teams[:2]
        match = self.get_match_1_1(teams)
        bv_mode = self.env.ref(
            "event_tournament.event_tournament_match_mode_beach_volley"
        )
        with self.assertRaises(UserError) as ue:
            match.action_done()
        for team in teams:
            self.assertIn(team.name, ue.exception.args[0])
        self.assertIn(bv_mode.name, ue.exception.args[0])
