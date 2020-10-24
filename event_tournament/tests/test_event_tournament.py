#  Copyright 2020 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import itertools
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.fields import first

from .test_common import COMPONENT_NBR, TEAM_NBR, TestCommon


class TestEventTournament(TestCommon):
    def test_onchange_event_id(self):
        """
        Change the event in the tournament,
        check that the tournament duration and court are now the same of the event.
        """
        tournament = first(self.tournaments)
        self.assertFalse(tournament.start_datetime)
        self.assertFalse(tournament.end_datetime)
        tournament.court_ids = self.court_model.browse()
        self.assertFalse(tournament.court_ids)

        tournament.onchange_event_id()
        event = tournament.event_id
        self.assertEqual(tournament.start_datetime, event.date_begin)
        self.assertEqual(tournament.end_datetime, event.date_end)
        self.assertEqual(tournament.court_ids, event.court_ids)

    def test_compute_match_count(self):
        """
        Create matches in the tournament,
        check that match_count correctly counts the matches.
        """
        tournament = first(self.tournaments)
        court = first(self.courts)
        tournament.court_ids = court

        self.assertFalse(tournament.match_count)
        self.match_model.create(
            {
                "tournament_id": tournament.id,
                "court_id": court.id,
                "team_ids": tournament.team_ids.ids,
            }
        )
        self.assertEqual(tournament.match_count, 1)

    def test_compute_match_count_estimated(self):
        """
        Create a tournament with teams,
        check that match_count_estimated is correctly computed.
        """
        tournament = first(self.tournaments)
        self.assertEqual(len(tournament.team_ids), TEAM_NBR)
        self.assertEqual(tournament.match_teams_nbr, 2)
        self.assertEqual(
            tournament.match_count_estimated,
            len(
                list(
                    itertools.combinations(
                        tournament.team_ids, tournament.match_teams_nbr
                    )
                )
            ),
        )
        self.team_model.create({"tournament_id": tournament.id, "name": "test"})
        self.assertEqual(
            tournament.match_count_estimated,
            len(
                list(
                    itertools.combinations(
                        tournament.team_ids, tournament.match_teams_nbr
                    )
                )
            ),
        )

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
        self.assertIn(tournament.name, ue.exception.args[0])

    def test_generate_matches_match_teams_nbr(self):
        """
        Create a tournament,
        check that at least 1 team per match is required for matches generation.
        """
        tournament = first(self.tournaments)
        tournament.match_teams_nbr = 0
        with self.assertRaises(UserError) as ue:
            tournament.generate_matches()
        self.assertIn(tournament.name, ue.exception.args[0])

    def test_generate_matches_duration(self):
        """
        Create a tournament,
        check that defining a duration for matches
        is required for matches generation.
        """
        tournament = first(self.tournaments)
        tournament.match_duration = 0
        tournament.match_warm_up_duration = 0
        with self.assertRaises(UserError) as ue:
            tournament.generate_matches()
        self.assertIn(tournament.name, ue.exception.args[0])

    def test_generate_matches_court(self):
        """
        Create a tournament,
        check that a court is required for matches generation.
        """
        tournament = first(self.tournaments)
        tournament.start_datetime = fields.Datetime.now()
        tournament.end_datetime = fields.Datetime.now() + timedelta(days=1)
        tournament.court_ids = self.court_model.browse()
        with self.assertRaises(UserError) as ue:
            tournament.generate_matches()
        self.assertIn(tournament.name, ue.exception.args[0])

    def test_generate_matches(self):
        """
        Create a tournament,
        check that all the estimated matches are created.
        """
        tournament = first(self.tournaments)
        tournament.randomize_matches_generation = True
        tournament.start_datetime = fields.Datetime.now()
        tournament.end_datetime = fields.Datetime.now() + timedelta(days=1)
        tournament.court_ids = self.courts
        matches = tournament.generate_matches()
        self.assertEqual(len(matches), tournament.match_count_estimated)

    def test_regenerate_matches(self):
        """
        Create a tournament,
        check that regenerating the matches keeps the done matches unchanged.
        """
        tournament = first(self.tournaments)
        tournament.randomize_matches_generation = True
        tournament.start_datetime = fields.Datetime.now()
        tournament.end_datetime = fields.Datetime.now() + timedelta(days=1)
        tournament.court_ids = self.courts
        matches = tournament.generate_matches()
        match = first(matches)
        match.update(self.get_match_lines_1_2(match.team_ids[:2]))
        match.action_done()

        new_matches = tournament.generate_matches()
        self.assertNotIn(match, new_matches)
        self.assertIn(match, tournament.match_ids)

    def test_action_draft(self):
        """
        Create a tournament,
        check that action_draft changes the state of the tournament.
        """
        tournament = first(self.tournaments)
        tournament.state = ""
        self.assertNotEqual(tournament.state, "draft")
        tournament.action_draft()
        self.assertEqual(tournament.state, "draft")

    def test_action_start(self):
        """
        Create a tournament,
        check that action_start changes the state of the tournament.
        """
        tournament = first(self.tournaments)
        tournament.state = ""
        self.assertNotEqual(tournament.state, "started")
        tournament.action_start()
        self.assertEqual(tournament.state, "started")

    def test_action_done(self):
        """
        Create a tournament,
        check that action_done changes the state of the tournament.
        """
        tournament = first(self.tournaments)
        tournament.state = ""
        self.assertNotEqual(tournament.state, "done")
        tournament.action_done()
        self.assertEqual(tournament.state, "done")

    def test_action_check_rules(self):
        """
        Create a tournament,
        check the rules for teams.
        """
        tournament = first(self.tournaments)
        tournament.min_components = COMPONENT_NBR + 1
        with self.assertRaises(ValidationError) as ve:
            tournament.action_check_rules()
        self.assertIn(tournament.name, str(ve.exception))
        tournament.min_components = 0
        tournament.action_check_rules()

    def test_action_view_matches(self):
        """
        Create a tournament,
        generate the matches and check that the action returned
        shows all the tournament's matches.
        """
        tournament = first(self.tournaments)
        tournament.randomize_matches_generation = True
        tournament.start_datetime = fields.Datetime.now()
        tournament.end_datetime = fields.Datetime.now() + timedelta(days=1)
        tournament.court_ids = self.courts

        action = tournament.generate_view_matches()
        matches = tournament.match_ids
        action_model = action.get("res_model")
        action_domain = action.get("domain")
        action_matches = self.env[action_model].search(action_domain)
        self.assertEqual(matches, action_matches)

    def test_action_view_teams(self):
        """
        Create a tournament,
        check that the method `action_view_teams`
        returns an action showing all the tournament's teams.
        """
        tournament = first(self.tournaments)
        teams = tournament.team_ids
        action = tournament.action_view_teams()
        action_model = action.get("res_model")
        action_domain = action.get("domain")
        action_teams = self.env[action_model].search(action_domain)
        self.assertEqual(teams, action_teams)

    def test_compute_components(self):
        """
        Create a tournament,
        check that the tournament's components equal
        the union of all the tournament's teams components.
        """
        tournament = first(self.tournaments)
        teams = tournament.team_ids
        self.assertEqual(teams.mapped("component_ids"), tournament.component_ids)

    def test_open_form_current(self):
        """
        Create a tournament,
        check that method `open_form_current`
        returns an action that shows the current tournament.
        """
        tournament = first(self.tournaments)
        action = tournament.open_form_current()
        action_model = action.get("res_model")
        action_id = action.get("res_id")
        action_tournament = self.env[action_model].browse(action_id)
        self.assertEqual(action_tournament, tournament)
