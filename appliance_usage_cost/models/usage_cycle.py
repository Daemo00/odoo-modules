#  Copyright 2024 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class UsageCycle(models.Model):
    _name = "appliance.usage.cost.usage.cycle"
    _description = "Execution of Program at specific date"
    _order = "start_date"

    program_id = fields.Many2one(
        comodel_name="appliance.usage.cost.appliance.program",
        required=True,
    )
    start_date = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
    )
    end_date = fields.Datetime(
        compute="_compute_end_date",
        store=True,
    )
    cost = fields.Float(
        compute="_compute_cost",
        store=True,
    )

    @api.depends()
    def _compute_display_name(self):
        return [
            (
                cycle.id,
                _(
                    "Execution of %(program)s at %(start_date)s",
                    program=cycle.program_id.name,
                    start_date=cycle.start_date,
                ),
            )
            for cycle in self
        ]

    @api.depends(
        "start_date",
        "program_id",
    )
    def _compute_end_date(self):
        for cycle in self:
            cycle.end_date = cycle.start_date + relativedelta(
                hours=cycle.program_id.duration,
            )

    def _get_cost_by_utility(self):
        """Dictionary mapping each consumed utility to its cost for this usage."""
        self.ensure_one()
        start, end = self.start_date, self.end_date
        total_duration_hours = (end - start).seconds // 3600
        utility_to_cost = dict()
        for utility_usage in self.program_id.utility_usage_ids:
            utility = utility_usage.utility_id
            contract = self.env[
                "appliance.usage.cost.utility.contract"
            ]._get_current_contract_for(utility, start_date=start)
            period_to_duration = contract._get_utility_period_duration(
                utility, start, end
            )

            # Suppose consumption is uniform in the period, and solve
            # duration : total_duration = X : total_quantity
            # -> X = duration * ( total_quantity / total_duration )
            quantity_per_hour = utility_usage.quantity / total_duration_hours
            period_to_quantity = {
                period: quantity_per_hour * duration
                for period, duration in period_to_duration.items()
            }

            period_to_cost = {
                period: period_quantity * period.cost
                for period, period_quantity in period_to_quantity.items()
            }

            utility_to_cost[utility] = sum(period_to_cost.values())

        return utility_to_cost

    @api.depends(
        "program_id",
        "start_date",
    )
    def _compute_cost(self):
        """Cost of all consumed utilities for this usage."""
        for cycle in self:
            utility_to_cost_dict = cycle._get_cost_by_utility()
            cycle.cost = sum(utility_to_cost_dict.values())
