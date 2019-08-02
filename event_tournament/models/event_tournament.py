#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class EventTournamentMatch(models.Model):
    _name = 'event.tournament'
    _description = "Tournament"
    _rec_name = 'name'

    name = fields.Char(
        required=True)
    event_id = fields.Many2one(
        comodel_name='event.event',
        string="Event")
    match_ids = fields.One2many(
        comodel_name='event.tournament.match',
        inverse_name='tournament_id',
        string="Matches")
    team_ids = fields.One2many(
        comodel_name='event.tournament.team',
        inverse_name='tournament_id',
        string="Teams")
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('done', "Done")],
        default='draft')
    min_components = fields.Integer(
        string="Minimum components",
        help="Minimum number of components for a team")
    max_components = fields.Integer(
        string="Maximum components",
        help="Maximum number of components for a team")
    min_components_female = fields.Integer(
        string="Minimum female components",
        help="Minimum number of female components for a team")
    min_components_male = fields.Integer(
        string="Minimum male components",
        help="Minimum number of male components for a team")

    @api.multi
    def action_done(self):
        for tournament in self:
            tournament.state = 'done'

    @api.multi
    def action_draft(self):
        for tournament in self:
            tournament.state = 'draft'

    @api.multi
    def action_check_rules(self):
        self.ensure_one()
        for team in self.team_ids:
            team.check_components_tournament(
                team.component_ids, self)
