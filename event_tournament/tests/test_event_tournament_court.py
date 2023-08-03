#  Copyright 2020 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import psycopg2

from odoo.fields import first
from odoo.tools import mute_logger

from .test_common import TestCommon


class TestEventTournamentCourt(TestCommon):
    def test_onchange_event_id(self):
        """
        Change the tournament in the court,
        check that the availability changes accordingly.
        """
        court = first(self.courts)
        self.assertFalse(court.time_availability_start)
        self.assertFalse(court.time_availability_end)

        court.onchange_event_id()
        event = court.event_id
        self.assertEqual(court.time_availability_start, event.date_begin)
        self.assertEqual(court.time_availability_end, event.date_end)

    def test_unique(self):
        """
        Create two courts with the same name,
        expect a Validation exception.
        """
        court = first(self.courts)
        with mute_logger("odoo.sql_db"), self.assertRaises(
            psycopg2.Error
        ) as unique_exc:
            self.court_model.create({"name": court.name, "event_id": court.event_id.id})
        # PG code for unique error
        self.assertEqual(unique_exc.exception.pgcode, "23505")

    def test_copy(self):
        """
        Copy a court,
        check that no exception is raised.
        """
        court = first(self.courts)
        self.assertTrue(court.copy())
