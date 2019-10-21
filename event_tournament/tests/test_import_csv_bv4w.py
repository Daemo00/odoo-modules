#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import os

from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_resource_path

from .test_common import TestCommon


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
        tournament_name = self.tournament_1.name
        self.tournament_1.unlink()
        with self.assertRaises(UserError) as ue:
            wizard.import_csv_bv4w()
        self.assertIn(tournament_name, ue.exception.name)

    def test_import_csv_bv4w_teams(self):
        """
        Import the file, check that the teams are created.
        """
        wizard = self.get_wizard_for_file('bv4w_test_1.csv')
        self.assertFalse(self.tournament_1.team_ids)
        wizard.import_csv_bv4w()
        self.assertEqual(len(self.tournament_1.team_ids), 2)

    def test_import_csv_bv4w_components(self):
        """
        Import the file, check that the components are created.
        """
        wizard = self.get_wizard_for_file('bv4w_test_1.csv')
        self.assertFalse(self.tournament_1.component_ids)
        wizard.import_csv_bv4w()
        self.assertEqual(len(self.tournament_1.event_id.registration_ids), 4)

    def test_import_csv_bv4w_components_overlap_error(self):
        """
        Import the file, check that the components are created
        and overlapping components from same tournaments raise exception.
        """
        wizard = self.get_wizard_for_file('bv4w_test_2.csv')
        self.assertFalse(self.tournament_1.component_ids)
        with self.assertRaises(ValidationError) as ue:
            wizard.import_csv_bv4w()
        self.assertIn(self.tournament_1.name, ue.exception.name)
        self.assertIn('test team 2', ue.exception.name)
        self.assertIn('TestTeamComponent2', ue.exception.name)

    def test_import_csv_bv4w_components_overlap(self):
        """
        Import the file, check that the components are created
        and overlapping components from different tournaments are merged.
        """
        wizard = self.get_wizard_for_file('bv4w_test_3.csv')
        self.assertFalse(self.tournament_1.component_ids)
        self.assertFalse(self.tournament_2.component_ids)
        wizard.import_csv_bv4w()
        self.assertEqual(len(self.tournament_1.component_ids), 2)
        self.assertEqual(len(self.tournament_2.component_ids), 2)
        self.assertEqual(len(self.event.registration_ids), 3)

    def test_import_csv_bv4w_components_homonym(self):
        """
        Import the file, check that the components are created
        and homonyms (born in different dates) are not merged.
        """
        wizard = self.get_wizard_for_file('bv4w_test_4.csv')
        self.assertFalse(self.tournament_1.component_ids)
        wizard.import_csv_bv4w()
        self.assertEqual(len(self.tournament_1.component_ids), 4)
