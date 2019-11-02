#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.exceptions import UserError
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
        """
        Create a tournament with teams,
        check that match_count_estimated is correctly computed.
        """
        tournament = first(self.tournaments)
        self.teams.update({'tournament_id': tournament.id})
        self.assertEqual(len(tournament.team_ids), 3)
        self.assertEqual(tournament.match_teams_nbr, 2)
        self.assertEqual(tournament.match_count_estimated, 3)
        self.team_model.create({
            'tournament_id': tournament.id,
            'name': 'test',
        })
        self.assertEqual(tournament.match_count_estimated, 6)

    def test_generate_matches_start_time(self):
        """
        Create a tournament,
        check that start time is required for matches generation.
        """
        tournament = first(self.tournaments)
        with self.assertRaises(UserError) as ue:
            self.assertTrue(tournament.generate_matches())
        self.assertIn(tournament.name, ue.exception.name)

    def test_generate_matches_court(self):
        """
        Create a tournament,
        check that a court is required for matches generation.
        """
        tournament = first(self.tournaments)
        tournament.start_datetime = fields.Datetime.now()
        with self.assertRaises(UserError) as ue:
            self.assertTrue(tournament.generate_matches())
        self.assertIn(tournament.name, ue.exception.name)

    def test_generate_matches(self):
        """
        Create a tournament,
        check that a court is required for matches generation.
        """
        tournament = self.tournaments[1]
        tournament.start_datetime = fields.Datetime.now()
        tournament.court_ids = self.court
        self.assertEqual(
            len(tournament.generate_matches()),
            tournament.match_count_estimated)
