#  Copyright 2020 ~ 2023 Simone Rubino <daemo00@gmail.com>
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
    teams_number = fields.Integer(
        compute="_compute_teams_number",
        store=True,
    )
    done_points = fields.Float(compute="_compute_teams_points", store=True)
    taken_points = fields.Float(compute="_compute_teams_points", store=True)
    points_ratio = fields.Float(compute="_compute_teams_points", store=True)
    won_sets = fields.Integer(compute="_compute_teams_points", store=True)
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
    date_open = fields.Datetime(
        string="Registration Date",
        readonly=True,
        default=lambda self: fields.Datetime.now(),
    )

    @api.depends(
        "tournament_team_ids",
    )
    def _compute_teams_number(self):
        for component in self:
            component.teams_number = len(component.tournament_team_ids)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            contact_id = self.partner_id.address_get().get("contact", False)
            if contact_id:
                contact = self.env["res.partner"].browse(contact_id)
                self.gender = contact.gender or self.gender
                self.birthdate_date = contact.birthdate_date or self.birthdate_date
                self.mobile = contact.mobile or self.mobile

    @api.depends(
        "tournament_team_ids.tournament_id",
    )
    def _compute_tournaments(self):
        for registration in self:
            registration.tournament_ids = registration.tournament_team_ids.mapped(
                "tournament_id"
            )

    @api.depends(
        "tournament_team_ids.done_points",
        "tournament_team_ids.taken_points",
        "tournament_team_ids.points_ratio",
        "tournament_team_ids.won_sets",
        "tournament_team_ids.matches_points",
        "tournament_team_ids.match_ids.state",
    )
    def _compute_teams_points(self):
        for registration in self:
            teams = registration.tournament_team_ids
            registration.done_points = sum(team.done_points for team in teams)
            registration.taken_points = sum(team.taken_points for team in teams)
            registration.points_ratio = registration.done_points / (
                registration.taken_points or 1
            )
            registration.won_sets = sum(team.won_sets for team in teams)
            registration.matches_points = sum(team.matches_points for team in teams)

            matches = teams.match_ids.filtered(lambda m: m.state == "done")
            registration.matches_done = len(matches)
