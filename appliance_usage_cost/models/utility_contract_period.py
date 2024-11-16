#  Copyright 2024 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    from calendar import Day
except ImportError:
    # The above import will work in 3.12,
    # see https://docs.python.org/3.12/library/calendar.html#calendar.Day
    import calendar
    from enum import Enum

    class Day(Enum):
        MONDAY = calendar.MONDAY
        TUESDAY = calendar.TUESDAY
        WEDNESDAY = calendar.WEDNESDAY
        THURSDAY = calendar.THURSDAY
        FRIDAY = calendar.FRIDAY
        SATURDAY = calendar.SATURDAY
        SUNDAY = calendar.SUNDAY


DAYS = {
    str(day_index): day_enum.name.capitalize() for day_index, day_enum in enumerate(Day)
}
# Days dictionary: {"0": "Monday", ...}


class UtilityContract(models.Model):
    """It is useful to think at periods geometrically:

    --------------------------------> days
    |        M  T  W  T  F  S  S
    |  00:00 |--------------|--|
    |        |              |  |
    |  07:00 |--------------|--|
    |        |              |  |
    |        |              |  |
    |  18:00 |--------------|--|
    |        |              |  |
    |  23:59 |--------------|--|
    |
    v hours

    More precisely it should be a Torus, but this is a good approximation for now.
    """

    _name = "appliance.usage.cost.utility.contract.period"
    _description = "Utility Contract Period"
    _order = "from_day, from_hour"

    name = fields.Char(
        required=True,
    )
    contract_id = fields.Many2one(
        comodel_name="appliance.usage.cost.utility.contract",
        ondelete="cascade",
        required=True,
    )
    utility_id = fields.Many2one(
        comodel_name="appliance.usage.cost.utility",
        required=True,
    )
    utility_uom_id = fields.Many2one(
        related="utility_id.uom_id",
        readonly=True,
    )
    from_day = fields.Selection(
        selection=list(DAYS.items()),
        required=True,
    )
    to_day = fields.Selection(
        selection=list(DAYS.items()),
        required=True,
    )
    from_hour = fields.Float(
        default=0,
        required=True,
    )
    to_hour = fields.Float(
        default=24,
        required=True,
    )
    cost = fields.Float()

    _sql_constraints = [
        (
            "hour_in_day",
            "CHECK("
            "0 <= from_hour AND from_hour <= 24 "
            "AND "
            "0 <= to_hour AND to_hour <= 24"
            ")",
            "Hour must be between 0 and 24 (included)",
        ),
        (
            "hour_order",
            "CHECK(from_hour < to_hour)",
            "From hour must be lower than To hour",
        ),
        (
            "day_order",
            "CHECK(from_day <= to_day)",
            "From day must be lower than To day",
        ),
    ]

    @api.constrains(
        "contract_id",
        "utility_id",
        "from_day",
        "to_day",
        "from_hour",
        "to_hour",
    )
    def _constrain_overlapping_periods(self):
        """Periods for the same contract and utility must not overlap."""
        pass

    def _includes(self, date):
        self.ensure_one()
        if isinstance(date, datetime):
            is_in_period = (
                int(self.from_day) <= date.weekday() <= int(self.to_day)
                and self.from_hour <= date.hour <= self.to_hour
            )
        else:
            is_in_period = False
        return is_in_period

    def _get_start_end(self, in_date):
        self.ensure_one()
        if self._includes(in_date):
            period_start_date = in_date - timedelta(
                days=in_date.weekday() - int(self.from_day),
                hours=in_date.hour - self.from_hour,
            )
            period_end_date = in_date + timedelta(
                days=int(self.to_day) - in_date.weekday(),
                hours=self.to_hour - in_date.hour,
            )
        else:
            raise UserError(
                _(
                    "%(in_date)s must be in period %(period)s",
                    in_date=in_date,
                    period=self.name,
                )
            )
        return period_start_date, period_end_date
