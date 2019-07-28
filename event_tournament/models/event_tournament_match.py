#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.fields import first


class EventTournamentMatch(models.Model):
    _name = 'event.tournament.match'
    _description = "Tournament match"

    tournament_id = fields.Many2one(
        comodel_name='event.tournament',
        string="Tournament")
    line_ids = fields.One2many(
        comodel_name='event.tournament.match.line',
        inverse_name='match_id',
        string="Teams")
    winner_team_id = fields.Many2one(
        comodel_name='event.tournament.team',
        string="Winner",
        states={'done': [
            ('required', True)]})
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('done', "Done")],
        default='draft')
    time_scheduled = fields.Datetime(
        string="Time scheduled")
    time_done = fields.Datetime(
        string="Time done")

    @api.constrains('line_ids')
    def constrain_teams(self):
        for match in self:
            match_lines = match.line_ids
            if len(match_lines) <= 1:
                raise ValidationError(_("A good match needs at least 2 teams"))
            registrations = first(match_lines).team_id.component_ids
            for team in match_lines.mapped('team_id'):
                registrations &= team.component_ids
            if registrations:
                raise ValidationError(_("Teams have common components"))

    @api.constrains('tournament_id', 'line_ids')
    def constrain_tournament(self):
        for match in self:
            teams_tournaments = match.line_ids.mapped('team_id.tournament_id')
            if len(teams_tournaments) > 1:
                raise ValidationError(_("Teams from different tournaments"))
            teams_tournament = first(teams_tournaments)
            if teams_tournament \
                    and teams_tournament != match.tournament_id:
                raise ValidationError(_("Teams not in selected tournament"))

    @api.constrains('winner_team_id', 'line_ids')
    def _constrain_winner(self):
        for match in self:
            if match.winner_team_id \
                    and match.winner_team_id not in match.line_ids.mapped('team_id'):
                raise ValidationError(
                    _("Winner team is not participating in this match"))

    @api.multi
    def action_draft(self):
        self.ensure_one()
        self.update({
            'winner_team_id': False,
            'time_done': False,
            'state': 'draft'})

    @api.multi
    def action_win(self, team):
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("Match already concluded"))
        self.update({
            'winner_team_id': team.id,
            'time_done': fields.Datetime.now(),
            'state': 'done'})

    @api.multi
    def name_get(self):
        res = list()
        for match in self:
            teams_names = match.line_ids.mapped('team_id.name')
            res.append((match.id, " vs ".join(teams_names)))
        return res


class EventTournamentMatchLine(models.Model):
    _name = 'event.tournament.match.line'
    _description = "Tournament match line"
    _rec_name = 'team_id'

    match_id = fields.Many2one(
        comodel_name='event.tournament.match',
        required=True,
        ondelete='cascade')
    team_id = fields.Many2one(
        comodel_name='event.tournament.team',
        required=True,
        ondelete='cascade')
    set_1 = fields.Integer()
    set_2 = fields.Integer()
    set_3 = fields.Integer()
    set_4 = fields.Integer()
    set_5 = fields.Integer()

    @api.multi
    def button_win(self):
        """This is clicked inside the tree of a match"""
        self.ensure_one()
        self.match_id.action_win(self.team_id)
