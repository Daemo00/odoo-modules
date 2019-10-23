#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import first
from .test_common import TestCommon


class TestEventTournament (TestCommon):

    def test_onchange_event_id(self):
        """
        Change the event in the tournament,
        check that the start_datetime is now the same of the event.
        """
        tournament = first(self.tournaments)
        self.assertFalse(tournament.start_datetime)
        self.assertFalse(tournament.court_ids)
        tournament.onchange_event_id()
        self.assertEqual(
            tournament.start_datetime,
            self.event.date_begin)
        self.assertEqual(
            tournament.court_ids,
            self.event.court_ids)

    def test_compute_match_count(self):
        """
        Create matches in the tournament,
        check that match_count correctly counts the matches.
        """
        tournament = first(self.tournaments)
        self.assertFalse(tournament.match_count)
        teams = self.team_model.create([
            {
                'tournament_id': tournament.id,
                'name': 'test team {team_index}'.format(team_index=team_index),
            }
            for team_index in range(2)])
        tournament.onchange_event_id()
        self.match_model.create({
            'tournament_id': tournament.id,
            'court_id': first(tournament.court_ids).id,
            'team_ids': teams.ids,
        })
        self.assertEqual(tournament.match_count, 1)

    def test_compute_match_count_estimated(self):
        tournament = first(self.tournaments)
        self.assertEqual(len(tournament.team_ids), 2)
        self.assertEqual(tournament.match_teams_nbr, 2)
        self.assertEqual(tournament.match_count_estimated, 1)
        self.team_model.create({
            'tournament_id': tournament.id,
            'name': 'test',
        })
        self.assertEqual(tournament.match_count_estimated, 3)
