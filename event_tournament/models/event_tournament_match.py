#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.fields import first


class EventTournamentMatch(models.Model):
    _name = 'event.tournament.match'
    _description = "Tournament match"

    tournament_id = fields.Many2one(
        comodel_name='event.tournament',
        string="Tournament")
    team_ids = fields.Many2many(
        comodel_name='event.tournament.team',
        string="Teams")
    winner_team_id = fields.Many2one(
        comodel_name='event.tournament.team',
        string="Winner",
        states={'done': [
            ('required', True)]})
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('done', "Done")])

    @api.constrains('team_ids')
    def constrain_teams(self):
        for match in self:
            registration = first(match.team_ids).component_ids
            for team in match.team_ids:
                registration &= team.component_ids
            if registration:
                raise ValidationError(_("Teams have common components"))

    @api.constrains('tournament_id', 'team_ids')
    def constrain_tournament(self):
        for match in self:
            teams_tournaments = match.team_ids.mapped('tournament_id')
            if len(teams_tournaments) > 1:
                raise ValidationError(_("Teams from different tournaments"))
            teams_tournament = first(teams_tournaments)
            if teams_tournament \
                    and teams_tournament != match.tournament_id:
                raise ValidationError(_("Teams not in selected tournament"))

    @api.constrains('team_ids', 'winner_team_id')
    def _constrain_winner(self):
        for match in self:
            if match.winner_team_id \
                    and match.winner_team_id not in match.team_ids:
                raise ValidationError(
                    _("Winner team is not participating in this match"))

    @api.multi
    def action_done(self):
        self.update({
            'state': 'done'})

    @api.multi
    def name_get(self):
        res = list()
        for match in self:
            match_name = match.team_ids.mapped('name')
            res.append((match.id, " vs ".join(match_name)))
        return res


