#  Copyright 2024 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import calendar
from datetime import datetime, timedelta

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestUsageCycle(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_same_period_cycle_cost(self):
        """A cycle during the same period has the correct cost."""
        # Arrange
        cycle_start_date = datetime(2020, month=1, day=1)
        electricity = self.env.ref("appliance_usage_cost.utility_electricity")
        water = self.env.ref("appliance_usage_cost.utility_water")
        program = self.env.ref(
            "appliance_usage_cost.appliance_program_washing_machine_eco"
        )
        cycle_end_date = cycle_start_date + timedelta(hours=program.duration)
        program_electricity_usage = program.utility_usage_ids.filtered(
            lambda usage: usage.utility_id == electricity
        )
        program_water_usage = program.utility_usage_ids.filtered(
            lambda usage: usage.utility_id == water
        )

        contract_electricity = self.env[
            "appliance.usage.cost.utility.contract"
        ]._get_current_contract_for(electricity, start_date=cycle_start_date)
        contract_electricity_period = contract_electricity.period_ids.filtered(
            lambda period: period._includes(cycle_start_date)
        )

        contract_water = self.env[
            "appliance.usage.cost.utility.contract"
        ]._get_current_contract_for(water, start_date=cycle_start_date)
        contract_water_period = contract_water.period_ids.filtered(
            lambda period: period._includes(cycle_start_date)
        )

        # pre-condition
        self.assertEqual(cycle_start_date.weekday(), calendar.WEDNESDAY)
        self.assertEqual(cycle_start_date.hour, 0)
        self.assertEqual(program.duration, 4)

        self.assertEqual(program_electricity_usage.quantity, 5)
        self.assertEqual(contract_electricity_period.cost, 10)
        self.assertTrue(contract_electricity_period._includes(cycle_end_date))

        self.assertEqual(program_water_usage.quantity, 20)
        self.assertTrue(contract_water_period._includes(cycle_end_date))
        self.assertEqual(contract_water_period.cost, 2)

        # Act
        cycle_form = Form(self.env["appliance.usage.cost.usage.cycle"])
        cycle_form.start_date = cycle_start_date
        cycle_form.program_id = program
        cycle = cycle_form.save()

        # Assert
        self.assertEqual(cycle.end_date, cycle_end_date)
        self.assertEqual(cycle.cost, 2 * 20 + 10 * 5)

    def test_mixed_period_cycle_cost(self):
        """A cycle across multiple periods has the correct cost."""
        # Arrange
        cycle_start_date = datetime(2020, month=1, day=3, hour=23)
        electricity = self.env.ref("appliance_usage_cost.utility_electricity")
        water = self.env.ref("appliance_usage_cost.utility_water")
        program = self.env.ref(
            "appliance_usage_cost.appliance_program_washing_machine_eco"
        )
        cycle_end_date = cycle_start_date + timedelta(hours=program.duration)
        program_electricity_usage = program.utility_usage_ids.filtered(
            lambda usage: usage.utility_id == electricity
        )
        program_water_usage = program.utility_usage_ids.filtered(
            lambda usage: usage.utility_id == water
        )

        contract_electricity = self.env[
            "appliance.usage.cost.utility.contract"
        ]._get_current_contract_for(electricity, start_date=cycle_start_date)
        contract_electricity_weekday_period = contract_electricity.period_ids.filtered(
            lambda period: period._includes(cycle_start_date)
        )
        contract_electricity_weekend_period = contract_electricity.period_ids.filtered(
            lambda period: period._includes(cycle_end_date)
        )

        contract_water = self.env[
            "appliance.usage.cost.utility.contract"
        ]._get_current_contract_for(water, start_date=cycle_start_date)
        contract_water_weekday_period = contract_water.period_ids.filtered(
            lambda period: period._includes(cycle_start_date)
        )
        contract_water_weekend_period = contract_water.period_ids.filtered(
            lambda period: period._includes(cycle_end_date)
        )

        # pre-condition
        self.assertEqual(cycle_start_date.weekday(), calendar.FRIDAY)
        self.assertEqual(cycle_start_date.hour, 23)
        self.assertEqual(program.duration, 4)

        self.assertEqual(program_electricity_usage.quantity, 5)
        self.assertEqual(contract_electricity_weekday_period.cost, 10)
        self.assertEqual(contract_electricity_weekend_period.cost, 5)

        self.assertEqual(program_water_usage.quantity, 20)
        self.assertEqual(contract_water_weekday_period.cost, 2)
        self.assertEqual(contract_water_weekend_period.cost, 1)

        # Act
        cycle_form = Form(self.env["appliance.usage.cost.usage.cycle"])
        cycle_form.start_date = cycle_start_date
        cycle_form.program_id = program
        cycle = cycle_form.save()

        # Assert
        self.assertEqual(cycle.end_date, cycle_end_date)
        self.assertEqual(
            cycle.cost, 1 / 4 * (2 * 20 + 10 * 5) + 3 / 4 * (1 * 20 + 5 * 5)
        )

    def test_multiple_weeks_cycle_cost(self):
        """A cycle across multiple weeks has the correct cost."""
        # Arrange
        cycle_start_date = datetime(2020, month=1, day=5, hour=23)
        electricity = self.env.ref("appliance_usage_cost.utility_electricity")
        water = self.env.ref("appliance_usage_cost.utility_water")
        program = self.env.ref(
            "appliance_usage_cost.appliance_program_washing_machine_eco"
        )
        cycle_end_date = cycle_start_date + timedelta(hours=program.duration)
        program_electricity_usage = program.utility_usage_ids.filtered(
            lambda usage: usage.utility_id == electricity
        )
        program_water_usage = program.utility_usage_ids.filtered(
            lambda usage: usage.utility_id == water
        )

        contract_electricity = self.env[
            "appliance.usage.cost.utility.contract"
        ]._get_current_contract_for(electricity, start_date=cycle_start_date)
        contract_electricity_weekend_period = contract_electricity.period_ids.filtered(
            lambda period: period._includes(cycle_start_date)
        )
        contract_electricity_weekday_period = contract_electricity.period_ids.filtered(
            lambda period: period._includes(cycle_end_date)
        )

        contract_water = self.env[
            "appliance.usage.cost.utility.contract"
        ]._get_current_contract_for(water, start_date=cycle_start_date)
        contract_water_weekend_period = contract_water.period_ids.filtered(
            lambda period: period._includes(cycle_start_date)
        )
        contract_water_weekday_period = contract_water.period_ids.filtered(
            lambda period: period._includes(cycle_end_date)
        )

        # pre-condition
        self.assertEqual(cycle_start_date.weekday(), calendar.SUNDAY)
        self.assertEqual(cycle_start_date.hour, 23)
        self.assertEqual(program.duration, 4)

        self.assertEqual(program_electricity_usage.quantity, 5)
        self.assertEqual(contract_electricity_weekend_period.cost, 5)
        self.assertEqual(contract_electricity_weekday_period.cost, 10)

        self.assertEqual(program_water_usage.quantity, 20)
        self.assertEqual(contract_water_weekend_period.cost, 1)
        self.assertEqual(contract_water_weekday_period.cost, 2)

        # Act
        cycle_form = Form(self.env["appliance.usage.cost.usage.cycle"])
        cycle_form.start_date = cycle_start_date
        cycle_form.program_id = program
        cycle = cycle_form.save()

        # Assert
        self.assertEqual(cycle.end_date, cycle_end_date)
        self.assertEqual(
            cycle.cost, 1 / 4 * (1 * 20 + 5 * 5) + 3 / 4 * (2 * 20 + 10 * 5)
        )
