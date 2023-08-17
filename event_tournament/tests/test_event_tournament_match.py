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
        match.action_done()
        stats = match.stats_ids.read(
            fields=[
                "team_id",
                "won_sets_count",
                "lost_sets_count",
                "done_points",
                "taken_points",
            ],
            load=None,
        )
        winner_stats = next(filter(lambda s: s["team_id"] == teams[1].id, stats))
        self.assertLess(
            {
                "won_sets_count": 2,
                "lost_sets_count": 1,
                "done_points": 54,
                "taken_points": 39,
            }.items(),
            winner_stats.items(),
        )

        loser_stats = next(filter(lambda s: s["team_id"] == teams[0].id, stats))
        self.assertLess(
            {
                "won_sets_count": 1,
                "lost_sets_count": 2,
                "done_points": 39,
                "taken_points": 54,
            }.items(),
            loser_stats.items(),
        )

    def test_action_done(self):
        """
        Create a match,
        check that the winner is correctly computed.
        """
        teams = self.teams[:2]
        match = self.get_match_1_2(teams)
        match.action_done()
        self.assertTrue(match.winner_team_ids == teams[1])
        with self.assertRaises(UserError) as ue, self.env.cr.savepoint():
            match.action_done()
        self.assertIn(match.display_name, ue.exception.args[0])
        self.assertIn("already done", ue.exception.args[0])

    def test_action_done_tie(self):
        """
        Create a match,
        check that ties are not allowed.
        """
        teams = self.teams[:2]
        match = self.get_match_1_1(teams)
        with self.assertRaises(UserError) as ue:
            with self.env.cr.savepoint():
                match.action_done()
        exc_message = ue.exception.args[0]
        self.assertIn(match.match_mode_id.display_name, exc_message)
        self.assertIn("1 - 1 not expected", exc_message)
        self.assertFalse(match.winner_team_ids)
