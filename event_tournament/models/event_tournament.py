#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import random
from datetime import timedelta
import itertools

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError


class EventTournament(models.Model):
    _name = 'event.tournament'
    _description = "Tournament"
    _rec_name = 'name'

    name = fields.Char(
        required=True)
    event_id = fields.Many2one(
        comodel_name='event.event',
        string="Event")
    court_ids = fields.Many2many(
        comodel_name='event.court',
        string="Courts",
        help="Courts available for this tournament")
    match_ids = fields.One2many(
        comodel_name='event.tournament.match',
        inverse_name='tournament_id',
        string="Matches")
    match_count = fields.Integer(
        string="Match count",
        compute='compute_match_count')
    team_ids = fields.One2many(
        comodel_name='event.tournament.team',
        inverse_name='tournament_id',
        string="Teams")
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('start', "Started"),
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
    start_datetime = fields.Datetime(
        string="Tournament start")
    match_duration = fields.Float(
        strin="Match duration")
    match_warm_up_duration = fields.Float(
        strin="Match warm-up duration")
    match_teams_nbr = fields.Integer(
        string="Teams per match",
        help="Number of teams per match",
        default=2)
    parent_id = fields.Many2one(
        comodel_name='event.tournament',
        string="Parent tournament")
    child_ids = fields.One2many(
        comodel_name='event.tournament',
        inverse_name='parent_id',
        string="Sub tournaments")
    notes = fields.Text(
        string="Notes")

    @api.multi
    @api.depends('match_ids')
    def compute_match_count(self):
        for tournament in self:
            tournament.match_count = len(tournament.match_ids)

    @api.multi
    def action_draft(self):
        for tournament in self:
            tournament.state = 'draft'

    @api.multi
    def action_start(self):
        for tournament in self:
            tournament.state = 'started'

    @api.multi
    def action_done(self):
        for tournament in self:
            tournament.state = 'done'

    @api.multi
    def action_check_rules(self):
        self.ensure_one()
        for team in self.team_ids:
            team.check_components_tournament(
                team.component_ids, self)

    @api.multi
    def generate_matches(self):
        self.ensure_one()
        match_model = self.env['event.tournament.match']
        matches = match_model.browse()
        matches_teams = list(itertools.combinations(
            self.team_ids, self.match_teams_nbr))
        # random.shuffle(matches_teams)
        courts = self.court_ids
        court_start = [
            (c, fields.Datetime.to_datetime(self.start_datetime))
            for c in courts]
        while matches_teams:
            match_teams = matches_teams.pop()
            # Sort the courts from the first free

            court_start.sort(key=lambda cs: cs[1])
            court_found, new_start = None, None
            # This is only checking the first match in the court
            for court, start_time in court_start:
                end_time = start_time + timedelta(hours=self.match_duration)
                # Check if one of the involved teams is playing somewhere else
                try:
                    matches |= match_model.create({
                        'tournament_id': self.id,
                        'court_id': court.id,
                        'line_ids': [(0, 0, {'team_id': t.id})
                                     for t in match_teams],
                        'time_scheduled_start': start_time,
                        'time_scheduled_end': end_time,
                    })
                    end_time = end_time + timedelta(
                        hours=self.match_warm_up_duration)
                    court_found = court
                    new_start = end_time
                    break
                except ValidationError:
                    # match.constrain_time has been triggered
                    continue
            else:
                # The match cannot fit in any court, put it back in top
                matches_teams.insert(0, match_teams)
            if court_found:
                new_court_start = list()
                for court, start in court_start:
                    if court == court_found:
                        new_court_start.append((court, new_start))
                    else:
                        new_court_start.append((court, start))
                court_start = new_court_start

        return matches

    @api.multi
    def action_view_matches(self):
        self.ensure_one()
        action = self.env.ref(
            'event_tournament.event_tournament_match_action').read()[0]
        action['domain'] = [('id', 'in', self.match_ids.ids)]
        return action