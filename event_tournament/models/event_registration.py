#  Copyright 2020 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EventRegistration(models.Model):
    _inherit = "event.registration"

    tournament_team_ids = fields.Many2many(
        comodel_name="event.tournament.team",
        string="Teams",
        relation="event_tournament_team_component_rel",
        column1="team_id",
        column2="component_id",
    )
    points_done = fields.Float(compute="_compute_teams_points", store=True)
    points_taken = fields.Float(compute="_compute_teams_points", store=True)
    points_ratio = fields.Float(compute="_compute_teams_points", store=True)
    sets_won = fields.Integer(compute="_compute_teams_points", store=True)
    matches_points = fields.Integer(compute="_compute_teams_points", store=True)
    matches_done = fields.Integer(compute="_compute_teams_points", store=True)
    tournament_ids = fields.Many2many(
        comodel_name="event.tournament", compute="_compute_tournaments", store=True
    )
    birthdate_date = fields.Date(string="Birthdate")
    gender = fields.Selection(
        selection=[("male", "Male"), ("female", "Female"), ("other", "Other")]
    )
    mobile = fields.Char()
    is_fipav = fields.Boolean(string="Is FIPAV")

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if self.partner_id:
            contact_id = self.partner_id.address_get().get("contact", False)
            if contact_id:
                contact = self.env["res.partner"].browse(contact_id)
                self.gender = contact.gender or self.gender
                self.birthdate_date = contact.birthdate_date or self.birthdate_date
                self.mobile = contact.mobile or self.mobile
        return res

    @api.depends(
        "tournament_team_ids.tournament_id",
    )
    def _compute_tournaments(self):
        for registration in self:
            registration.tournament_ids = registration.tournament_team_ids.mapped(
                "tournament_id"
            )

    @api.depends(
        "tournament_team_ids.points_done",
        "tournament_team_ids.points_taken",
        "tournament_team_ids.points_ratio",
        "tournament_team_ids.sets_won",
        "tournament_team_ids.matches_points",
        "tournament_team_ids.match_ids.state",
    )
    def _compute_teams_points(self):
        for registration in self:
            teams = registration.tournament_team_ids
            registration.points_done = sum(team.points_done for team in teams)
            registration.points_taken = sum(team.points_taken for team in teams)
            registration.points_ratio = registration.points_done / (
                registration.points_taken or 1
            )
            registration.sets_won = sum(team.sets_won for team in teams)
            registration.matches_points = sum(team.matches_points for team in teams)

            matches = teams.match_ids.filtered(lambda m: m.state == "done")
            registration.matches_done = len(matches)
