#  Copyright 2022 Simone Rubino
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class EventRegistration(models.Model):
    _inherit = "event.registration"

    def _get_website_registration_allowed_fields(self):
        allowed_fields = super()._get_website_registration_allowed_fields()
        allowed_fields.update(
            {
                "birthdate_date",
                "gender",
                "mobile",
                "is_fipav",
            }
        )
        return allowed_fields
