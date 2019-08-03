#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.fields import first


class EventTournamentMatch(models.Model):
    _name = 'event.tournament.match'
    _description = "Tournament match"
    _order = 'time_scheduled_start'

    tournament_id = fields.Many2one(
        comodel_name='event.tournament',
        string="Tournament",
        required=True)
    court_id = fields.Many2one(
        comodel_name='event.court',
        string="Court",
        required=True)
    line_ids = fields.One2many(
        comodel_name='event.tournament.match.line',
        inverse_name='match_id',
        string="Teams")
    winner_team_id = fields.Many2one(
        comodel_name='event.tournament.team',
        string="Winner")
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('done', "Done")],
        default='draft')
    time_scheduled_start = fields.Datetime(
        string="Scheduled start")
    time_scheduled_end = fields.Datetime(
        string="Scheduled end")
    time_done = fields.Datetime(
        string="Time done")

    @api.onchange('tournament_id')
    def onchange_tournament(self):
        event_domain = [('event_id', '=', self.tournament_id.event_id.id)]
        return {
            'domain': {
                'court_id': event_domain}}

    @api.constrains('time_scheduled_start', 'time_scheduled_end')
    def constrain_time(self):
        for match in self:
            contemporary_matches_domain = [
                ('time_scheduled_start', '<=', match.time_scheduled_end),
                ('time_scheduled_end', '>=', match.time_scheduled_start)]
            contemporary_matches = self.search(contemporary_matches_domain)
            contemporary_matches = contemporary_matches - match
            match_components = match.line_ids.mapped('team_id.component_ids')
            for cont_match in contemporary_matches:
                cont_match_comps = cont_match.line_ids \
                    .mapped('team_id.component_ids')
                for cont_match_comp in cont_match_comps:
                    if cont_match_comp in match_components:
                        raise ValidationError(_(
                            "Match {match_name} not valid:\n"
                            "Component {comp_name} is already playing "
                            "in match {cont_match_name}.")
                            .format(
                                match_name=match.display_name,
                                comp_name=cont_match_comp.display_name,
                                cont_match_name=cont_match.display_name))

    @api.constrains('tournament_id', 'court_id')
    def constrain_court(self):
        for match in self:
            if match.court_id not in match.tournament_id.court_ids:
                raise ValidationError(
                    _("Match {match_name} not valid:\n"
                      "Court {court_name} is not available for "
                      "tournament {tourn_name}")
                    .format(
                        match_name=match.display_name,
                        court_name=match.court_id.display_name,
                        tourn_name=match.tournament_id.display_name))

    @api.constrains('line_ids')
    def constrain_teams(self):
        for match in self:
            match_lines = match.line_ids
            if len(match_lines) <= 1:
                raise ValidationError(_("A good match needs at least 2 teams"))
            teams = match_lines.mapped('team_id')
            registrations = self.env['event.registration'].browse()
            for team in teams:
                registrations &= team.component_ids
            if registrations:
                raise ValidationError(
                    _("Match {match_name} not valid:\n"
                      "Teams have common components")
                    .format(
                        match_name=match.display_name))

    @api.constrains('tournament_id', 'line_ids')
    def constrain_tournament(self):
        for match in self:
            teams_tournaments = match.line_ids.mapped('team_id.tournament_id')
            if len(teams_tournaments) > 1:
                raise ValidationError(
                    _("Match {match_name} not valid:\n"
                      "Teams from different tournaments")
                    .format(
                        match_name=match.display_name))
            teams_tournament = first(teams_tournaments)
            if teams_tournament \
                    and teams_tournament != match.tournament_id:
                raise ValidationError(
                    _("Match {match_name} not valid:\n"
                      "Teams not in tournament {tourn_name}.")
                    .format(
                        match_name=match.display_name,
                        tourn_name=match.tournament_id.display_name))

    @api.constrains('winner_team_id', 'line_ids')
    def _constrain_winner(self):
        for match in self:
            if not match.winner_team_id:
                continue
            teams = match.line_ids.mapped('team_id')
            if match.winner_team_id not in teams:
                raise ValidationError(
                    _("Match {match_name} not valid:\n"
                      "winner team {team_name} is not participating.")
                    .format(
                        match_name=match.display_name,
                        team_name=match.winner_team_id.display_name))

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
            raise UserError(_("Match {match_name} already done")
                            .format(match_name=self.display_name))
        self.update({
            'winner_team_id': team.id,
            'time_done': fields.Datetime.now(),
            'state': 'done'})

    @api.multi
    def name_get(self):
        res = list()
        for match in self:
            teams_names = match.line_ids.mapped('team_id.name')
            match_name = " vs ".join(teams_names)
            res.append((match.id, match_name))
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
        required=True)
    set_1 = fields.Integer()
    set_2 = fields.Integer()
    set_3 = fields.Integer()
    set_4 = fields.Integer()
    set_5 = fields.Integer()

    @api.multi
    def action_win(self):
        self.ensure_one()
        self.match_id.action_win(self.team_id)
