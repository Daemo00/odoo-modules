#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import itertools

from odoo import fields
from odoo.exceptions import UserError
from odoo.fields import first
from .test_common import TestCommon, TEAM_NBR, TOURNAMENT_NBR, EVENT_NBR


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
        event = first(self.events)
        self.assertEqual(tournament.start_datetime, event.date_begin)
        self.assertEqual(tournament.court_ids, event.court_ids)

    def test_compute_match_count(self):
        """
        Create matches in the tournament,
        check that match_count correctly counts the matches.
        """
        tournament = first(self.tournaments)
        teams = self.teams
        court = first(self.courts)
        tournament.court_ids = court
        teams.update({'tournament_id': tournament.id})

        self.assertFalse(tournament.match_count)
        self.match_model.create({
            'tournament_id': tournament.id,
            'court_id': court.id,
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
        self.assertEqual(len(tournament.team_ids),
                         EVENT_NBR * TOURNAMENT_NBR * TEAM_NBR)
        self.assertEqual(tournament.match_teams_nbr, 2)
        self.assertEqual(tournament.match_count_estimated,
                         len(list(itertools.combinations(
                             tournament.team_ids,
                             tournament.match_teams_nbr))))
        self.team_model.create({
            'tournament_id': tournament.id,
            'name': 'test',
        })
        self.assertEqual(tournament.match_count_estimated,
                         len(list(itertools.combinations(
                             tournament.team_ids,
                             tournament.match_teams_nbr))))

    def test_compute_team_count(self):
        """
        Create a tournament with teams,
        check that team_count is correctly computed.
        """
        tournament = first(self.tournaments)
        self.assertEqual(len(tournament.team_ids), tournament.team_count)

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
        check that all the estimated matches are created.
        """
        tournament = first(self.tournaments)
        tournament.randomize_matches_generation = True
        tournament.start_datetime = fields.Datetime.now()
        tournament.court_ids = self.courts
        self.assertEqual(
            len(tournament.generate_matches()),
            tournament.match_count_estimated)

    def test_action_draft(self):
        """
        Create a tournament,
        check that action_draft changes the state of the tournament.
        """
        tournament = first(self.tournaments)
        tournament.state = ''
        tournament.action_draft()
        self.assertEqual(tournament.state, 'draft')

    def test_action_start(self):
        """
        Create a tournament,
        check that action_start changes the state of the tournament.
        """
        tournament = first(self.tournaments)
        tournament.state = ''
        tournament.action_start()
        self.assertEqual(tournament.state, 'started')

    def test_action_done(self):
        """
        Create a tournament,
        check that action_done changes the state of the tournament.
        """
        tournament = first(self.tournaments)
        tournament.state = ''
        tournament.action_done()
        self.assertEqual(tournament.state, 'done')
