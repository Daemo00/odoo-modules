#  Copyright 2024 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from itertools import cycle

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class UtilityContract(models.Model):
    _name = "appliance.usage.cost.utility.contract"
    _description = "Utility Contract"

    name = fields.Char(
        required=True,
    )
    start_date = fields.Date(
        required=True,
    )
    end_date = fields.Date(
        required=True,
    )
    period_ids = fields.One2many(
        comodel_name="appliance.usage.cost.utility.contract.period",
        inverse_name="contract_id",
        string="Periods",
    )

    def _get_utility_period_duration(self, utility, from_date, to_date):
        """Periods used between `from_date` and `to_date` for `utility`.

        Return a dictionary mapping each period to how much it has been used for.
        """
        utility_periods = self.period_ids.filtered(
            lambda period, util=utility: period.utility_id == util
        )
        result = dict()
        current_date = from_date
        for utility_period in cycle(utility_periods.sorted()):
            if utility_period._includes(current_date):
                period_start_date, period_end_date = utility_period._get_start_end(
                    current_date
                )
                slot_end = min(to_date, period_end_date)
                duration = slot_end - current_date
                result[utility_period] = duration.seconds / 3600
                if slot_end == to_date:
                    break
                else:
                    current_date = slot_end
        return result

    @api.model
    def _get_current_contract_for(self, utility, start_date=None):
        """Cost of `utility` between dates."""
        if start_date is None:
            start_date = date.today()
        active_contract = self.search(
            [
                ("period_ids.utility_id", "in", utility.ids),
                ("start_date", "<=", start_date),
                ("end_date", ">=", start_date),
            ],
        )

        if len(active_contract) > 1:
            raise UserError(
                _(
                    "Multiple contracts for %(utility) found for %(day)s",
                    utility=utility.name,
                    day=start_date,
                )
            )
        elif not active_contract:
            raise UserError(
                _(
                    "No contract for %(utility)s found for %(day)s",
                    utility=utility.name,
                    day=start_date,
                )
            )

        active_contract.ensure_one()
        return active_contract
