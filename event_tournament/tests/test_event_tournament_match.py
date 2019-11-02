#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .test_common import TestCommon


class TestEventTournamentMatch (TestCommon):

    def test_get_sets_info(self):
        """
        Create a match,
        check that sets info are correctly computed.
        """
        teams = self.teams[:2]
        match = self.get_match_2_1(teams)
        self.assertDictEqual(
            {
                teams[0]: (1, 39, 54),
                teams[1]: (2, 54, 39),
            }
            , match.get_sets_info())
