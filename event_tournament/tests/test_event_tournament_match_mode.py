#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .test_common import TestCommon


class TestEventTournamentMatchMode (TestCommon):

    def test_get_points(self):
        teams = self.teams[:2]
        match = self.get_match(teams)
        bv_mode = self.env.ref('event_tournament.'
                               'event_tournament_match_mode_beach_volley')
        self.assertDictEqual(
            {
                teams[0]: 1,
                teams[1]: 2,
            }
            , bv_mode.get_points(match)
        )
