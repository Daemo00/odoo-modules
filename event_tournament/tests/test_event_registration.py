#  Copyright 2019 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Command, first
from odoo.tests import Form

from .test_common import TestCommon


class TestEventRegistration(TestCommon):
    def setUp(self):
        super().setUp()
        self.components = self.component_model.create(
            [
                {"event_id": first(self.events).id},
                {"event_id": first(self.events).id},
            ]
        )

    def test_onchange_partner_id(self):
        """
        Assign a partner to the component,
        check that the gender is propagated from the partner to the component.
        """
        partner = self.env["res.partner"].create(
            {"name": "test partner", "gender": "male"}
        )
        component = first(self.components)
        self.assertFalse(component.gender)
        with Form(component) as ccomponent_form:
            ccomponent_form.partner_id = partner
        self.assertEqual(component.gender, partner.gender)

    def test_compute_tournaments(self):
        """
        Assign a team to the component,
        check that the component is in the team's tournament.
        """
        components = self.components
        self.assertFalse(components.tournament_team_ids)
        tournament = first(self.tournaments)
        team = self.team_model.create(
            {
                "event_id": first(self.events).id,
                "tournament_id": tournament.id,
                "name": "test team",
                "component_ids": [Command.set(components.ids)],
            }
        )
        self.assertIn(team, components.tournament_team_ids)
        self.assertTrue(
            all(component in tournament.component_ids for component in components)
        )
