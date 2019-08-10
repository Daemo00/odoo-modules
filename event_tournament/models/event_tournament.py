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
    randomize_matches_generation = fields.Boolean(
        string="Randomize",
        help="Randomize matches generation")
    reset_matches_before_generation = fields.Boolean(
        string="Reset",
        help="Reset matches before generation",
        default=True)
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
        if self.randomize_matches_generation:
            random.shuffle(matches_teams)
        if self.reset_matches_before_generation:
            self.match_ids.unlink()

        warm_up_start = self.start_datetime \
            - timedelta(hours=self.match_warm_up_duration)
        min_start = warm_up_start
        max_start = warm_up_start

        match_duration = \
            timedelta(hours=self.match_warm_up_duration) \
            + timedelta(hours=self.match_duration)
        while matches_teams:
            match_teams = matches_teams.pop()
            match = match_model.browse()
            curr_start = min_start
            # Try to schedule the match as soon as possible
            while curr_start <= max_start:
                # Try to put this match in a court at curr_start
                for court in self.court_ids:
                    try:
                        # The first match of the court does not need warm-up
                        match = match_model.create({
                            'tournament_id': self.id,
                            'court_id': court.id,
                            'line_ids': [(0, 0, {'team_id': t.id})
                                         for t in match_teams],
                            'time_scheduled_start': curr_start,
                            'time_scheduled_end': curr_start + match_duration,
                        })
                    except ValidationError as ve:
                        # The match is not valid,
                        # but it has been created anyway! So delete it.
                        invalid_match = match_model.search(
                            [], order='id DESC', limit=1)
                        invalid_match.unlink()
                        # Try the following court
                        continue
                    else:
                        # The match is valid
                        matches |= match
                        break
                else:
                    # The match could not be scheduled in any court,
                    # try another time
                    pass

                if match:
                    break
                else:
                    curr_start = curr_start + match_duration
            if not match:
                raise UserError(_("Scheduling impossibru for a match between ")
                                + ", ".join(team.display_name
                                            for team in match_teams))
            max_start = max(max_start, match.time_scheduled_end)

        return matches

    @api.multi
    def action_view_matches(self):
        self.ensure_one()
        action = self.env.ref(
            'event_tournament.event_tournament_match_action').read()[0]
        action['domain'] = [('id', 'in', self.match_ids.ids)]
        return action
