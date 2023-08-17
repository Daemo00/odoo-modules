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
    tournament_match_ids = fields.Many2many(
        comodel_name="event.tournament.match",
        related="tournament_team_ids.match_ids",
        string="Matches",
        relation="event_tournament_match_component_rel",
        column1="match_id",
        column2="component_id",
    )
    teams_number = fields.Integer(
        compute="_compute_teams_number",
        store=True,
    )
    tournament_ids = fields.Many2many(
        comodel_name="event.tournament", compute="_compute_tournaments", store=True
    )
    tournament_stats_ids = fields.Many2many(
        comodel_name="event.tournament.match.team_stats",
        compute="_compute_tournament_stats_ids",
        store=True,
    )
    done_points = fields.Integer(compute="_compute_tournament_stats_ids", store=True)
    taken_points = fields.Integer(compute="_compute_tournament_stats_ids", store=True)
    won_set_ids = fields.Many2many(
        comodel_name="event.tournament.match.set",
        compute="_compute_tournament_stats_ids",
        relation="event_tournament_registration_won_set_rel",
        column1="registration_id",
        column2="set_id",
        store=True,
    )
    won_sets_count = fields.Integer(compute="_compute_tournament_stats_ids", store=True)
    lost_set_ids = fields.Many2many(
        comodel_name="event.tournament.match.set",
        compute="_compute_tournament_stats_ids",
        relation="event_tournament_registration_lost_set_rel",
        column1="registration_id",
        column2="set_id",
        store=True,
    )
    lost_sets_count = fields.Integer(
        compute="_compute_tournament_stats_ids", store=True
    )
    tournament_points = fields.Integer(
        compute="_compute_tournament_stats_ids", store=True
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
    sets_ratio = fields.Float(compute="_compute_sets_ratio", store=True, digits=(16, 5))
    points_ratio = fields.Float(
        compute="_compute_points_ratio", store=True, digits=(16, 5)
    )

    @api.depends(
        "tournament_stats_ids.done_points",
        "tournament_stats_ids.taken_points",
    )
    def _compute_points_ratio(self):
        for registration in self:
            registration.points_ratio = (
                registration.tournament_team_ids.stats_ids.get_points_ratio()
            )

    @api.depends(
        "tournament_stats_ids.lost_sets_count",
        "tournament_stats_ids.won_sets_count",
    )
    def _compute_sets_ratio(self):
        for registration in self:
            registration.sets_ratio = (
                registration.tournament_team_ids.stats_ids.get_sets_ratio()
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
        "tournament_match_ids.state",
        "tournament_team_ids.stats_ids.done_points",
        "tournament_team_ids.stats_ids.taken_points",
        "tournament_team_ids.stats_ids.won_set_ids",
        "tournament_team_ids.stats_ids.won_sets_count",
        "tournament_team_ids.stats_ids.lost_set_ids",
        "tournament_team_ids.stats_ids.lost_sets_count",
        "tournament_team_ids.stats_ids.tournament_points",
    )
    def _compute_tournament_stats_ids(self):
        for registration in self:
            teams = registration.tournament_team_ids
            stats = teams.stats_ids
            registration.tournament_stats_ids = stats

            if stats:
                done_points = sum(stats.mapped("done_points"))
                taken_points = sum(stats.mapped("taken_points"))
                won_sets_count = sum(stats.mapped("won_sets_count"))
                lost_sets_count = sum(stats.mapped("lost_sets_count"))
                tournament_points = sum(stats.mapped("tournament_points"))
            else:
                done_points = 0
                taken_points = 0
                won_sets_count = 0
                lost_sets_count = 0
                tournament_points = 0

            registration.done_points = done_points
            registration.taken_points = taken_points
            registration.won_set_ids = stats.won_set_ids
            registration.won_sets_count = won_sets_count
            registration.lost_set_ids = stats.lost_set_ids
            registration.lost_sets_count = lost_sets_count
            registration.tournament_points = tournament_points

    def button_compute_tournament_stats_ids(self):
        """Public method (callable from UI) for computing match's points."""
        self._compute_tournament_stats_ids()
