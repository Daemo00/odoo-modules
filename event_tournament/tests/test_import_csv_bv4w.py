#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import os

from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_resource_path
from .test_common import TestCommon, TEAM_NBR


class TestImportCsvBV4W (TestCommon):

    def setUp(self):
        super().setUp()
        self.wizard_model = self.env['event.tournament.import_csv_bv4w']

    def get_wizard_for_file(self, file_name):
        resp_path = get_resource_path(
            self.test_module, 'tests', 'data', file_name)
        with open(resp_path, 'rb') as resp_file:
            wizard = self.wizard_model.create({
                'data': base64.encodebytes(resp_file.read()),
                'filename': os.path.basename(resp_file.name),
            })
        return wizard

    def test_import_csv_bv4w_no_tournament(self):
        """
        Import the file when no tournament exists,
        an exception should be raised.
        """
        wizard = self.get_wizard_for_file('bv4w_test_1.csv')
        tournament = self.tournaments.filtered(
            lambda t: t.name in ['event 0, tournament 0'])
        tournament_name = tournament.name
        tournament.unlink()
        with self.assertRaises(UserError) as ue:
            wizard.import_csv_bv4w()
        self.assertIn(tournament_name, ue.exception.name)

    def test_import_csv_bv4w_teams(self):
        """
        Import the file, check that the teams are created.
        """
        wizard = self.get_wizard_for_file('bv4w_test_1.csv')
        tournament = self.tournaments.filtered(
            lambda t: t.name in ['event 0, tournament 0'])
        self.assertEqual(len(tournament.team_ids), TEAM_NBR)
        wizard.import_csv_bv4w()
        self.assertEqual(len(tournament.team_ids), 2 + TEAM_NBR)

    def test_import_csv_bv4w_components(self):
        """
        Import the file, check that the components are created.
        """
        wizard = self.get_wizard_for_file('bv4w_test_1.csv')
        tournament = self.tournaments.filtered(
            lambda t: t.name in ['event 0, tournament 0'])
        tournament.component_ids.unlink()
        wizard.import_csv_bv4w()
        self.assertEqual(len(tournament.component_ids), 4)

    def test_import_csv_bv4w_components_overlap_error(self):
        """
        Import the file, check that the components are created
        and overlapping components from same tournaments raise exception.
        """
        wizard = self.get_wizard_for_file('bv4w_test_2.csv')
        tournament = self.tournaments.filtered(
            lambda t: t.name in ['event 0, tournament 0'])
        tournament.component_ids = self.component_model.browse()
        with self.assertRaises(ValidationError) as ue:
            wizard.import_csv_bv4w()
        self.assertIn(tournament.name, ue.exception.name)
        self.assertIn('test team 2', ue.exception.name)
        self.assertIn('TestTeamComponent2', ue.exception.name)

    def test_import_csv_bv4w_components_overlap(self):
        """
        Import the file, check that the components are created
        and overlapping components from different tournaments are merged.
        """
        wizard = self.get_wizard_for_file('bv4w_test_3.csv')
        tournaments = self.tournaments.filtered(
            lambda t: t.name in ['event 0, tournament 0',
                                 'event 0, tournament 1'])
        tournaments.mapped('component_ids').unlink()

        wizard.import_csv_bv4w()
        for tournament in tournaments:
            self.assertEqual(len(tournament.component_ids), 2)
        components = tournaments.mapped('component_ids')
        self.assertEqual(len(components), 3)

    def test_import_csv_bv4w_components_homonym(self):
        """
        Import the file, check that the components are created
        and homonyms (born in different dates) are not merged.
        """
        wizard = self.get_wizard_for_file('bv4w_test_4.csv')
        tournament = self.tournaments.filtered(
            lambda t: t.name in ['event 0, tournament 0'])
        tournament.component_ids.unlink()
        wizard.import_csv_bv4w()
        self.assertEqual(len(tournament.component_ids), 4)
