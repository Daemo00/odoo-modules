#  Copyright 2022 Simone Rubino
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import logging

_logger = logging.getLogger(__name__)


class EventTournament(models.Model):
    _inherit = "event.tournament"

    website_description = fields.Html(
        translate=True,
    )
