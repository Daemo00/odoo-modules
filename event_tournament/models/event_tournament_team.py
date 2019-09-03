#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.fields import first


class EventTournamentTeam (models.Model):
    _name = 'event.tournament.team'
    _description = "Tournament team"
    _rec_name = 'name'
    _order = 'matches_points desc, sets_won desc, points_ratio desc'

    event_id = fields.Many2one(
        related='tournament_id.event_id',
        readonly=True)
    tournament_id = fields.Many2one(
        comodel_name='event.tournament',
        string="Tournament",
        required=True,
        ondelete='cascade')
    name = fields.Char(
        required=True)
    component_ids = fields.Many2many(
        comodel_name='event.registration',
        string="Components")
    match_ids = fields.Many2many(
        comodel_name='event.tournament.match',
        string="Matches")
    points_ratio = fields.Float(
        compute='compute_matches_points',
        store=True)
    sets_won = fields.Integer(
        compute='compute_matches_points',
        store=True)
    matches_points = fields.Integer(
        compute='compute_matches_points',
        store=True)

    @api.onchange('tournament_id')
    def onchange_tournament(self):
        components_domain = [
            ('event_id', '=', self.event_id.id),
            ('tournament_ids', 'not in', self.tournament_id.id)]
        matches_domain = [('tournament_id', '=', self.tournament_id.id)]
        return {
            'domain': {
                'component_ids': components_domain,
                'match_ids': matches_domain}}

    @api.multi
    @api.constrains('component_ids', 'event_id')
    def constrain_components_event(self):
        for team in self:
            components = team.component_ids
            event = team.event_id
            if not components or not event:
                continue
            components_events = components.mapped('event_id')
            if len(components_events) > 1:
                raise ValidationError(_(
                    "Team {team_name} not valid:\n"
                    "Components from different events")
                    .format(
                        team_name=team.display_name))
            components_event = first(components_events)
            if components_event != event:
                raise ValidationError(_(
                    "Team {team_name} not valid:\n"
                    "Components not in event {event_name}.")
                    .format(
                        team_name=team.display_name,
                        event_name=event.display_name))

    @api.multi
    @api.constrains('component_ids', 'tournament_id')
    def constrain_components_tournament(self):
        for team in self:
            components = team.component_ids
            tournament = team.tournament_id
            if not components or not tournament:
                continue
            for other_team in tournament.team_ids - team:
                for component in components:
                    if component in other_team.component_ids:
                        raise ValidationError(_(
                            "Team {team_name} not valid:\n"
                            "component {comp_name} is already in "
                            "team {other_team_name}.")
                            .format(
                                team_name=team.display_name,
                                comp_name=component.display_name,
                                other_team_name=other_team.display_name))
            if tournament.min_components \
                    and len(components) < tournament.min_components:
                raise ValidationError(_(
                    "Team {team_name} not valid:\n"
                    "tournament {tourn_name} requires "
                    "at least {min_comp} components per team.")
                    .format(
                        team_name=team.display_name,
                        tourn_name=tournament.display_name,
                        min_comp=tournament.min_components))
            if tournament.max_components \
                    and len(components) > tournament.max_components:
                raise ValidationError(_(
                    "Team {team_name} not valid:\n"
                    "tournament {tourn_name} requires "
                    "at least {max_comp} components per team.")
                    .format(
                        team_name=team.display_name,
                        tourn_name=tournament.display_name,
                        max_comp=tournament.max_components))
            if tournament.min_components_female \
                    or tournament.min_components_male:
                if not all(c.gender for c in components):
                    raise ValidationError(_(
                        "Team {team_name} not valid:\n"
                        "tournament {tourn_name} requires "
                        "a minimum of female (or male) components but "
                        "not all components have gender.")
                        .format(
                            team_name=team.display_name,
                            tourn_name=tournament.display_name))
                if tournament.min_components_female:
                    female_components = components.filtered(
                        lambda c: c.gender == 'female')
                    if len(female_components) > \
                            tournament.min_components_female:
                        raise ValidationError(_(
                            "Team {team_name} not valid:\n"
                            "tournament {tourn_name} requires at least "
                            "{min_female_comp} female components per team.")
                            .format(
                                team_name=team.display_name,
                                tourn_name=tournament.display_name,
                                min_female_comp=tournament
                                .min_components_female))
                if tournament.min_components_male:
                    male_components = components.filtered(
                        lambda c: c.gender == 'male')
                    if len(male_components) > tournament.min_components_male:
                        raise ValidationError(_(
                            "Team {team_name} not valid:\n"
                            "tournament {tourn_name} requires at least "
                            "{min_male_comp} male components per team.")
                            .format(
                                team_name=team.display_name,
                                tourn_name=tournament.display_name,
                                min_male_comp=tournament.min_components_male))

    @api.multi
    @api.depends(lambda m:
                 ('match_ids.state',
                  'tournament_id.match_mode_id')
                 + tuple('match_ids.line_ids.set_' + str(n)
                         for n in range(1, 6)))
    def compute_matches_points(self):
        set_fields = ['set_' + str(n) for n in range(1, 6)]
        for team in self:
            matches_points = 0
            total_sets_won = 0
            points_done = 0
            points_taken = 0
            match_mode = team.tournament_id.match_mode_id
            done_matches = team.match_ids.filtered(lambda m: m.state == 'done')
            for match in done_matches:
                sets_won = 0
                sets_lost = 0
                for set_field in set_fields:
                    team_points = 0
                    other_team_points = 0
                    for line in match.line_ids:
                        points = getattr(line, set_field)
                        if line.team_id == team:
                            team_points += points
                        else:
                            other_team_points += points
                    if team_points or other_team_points:
                        if team_points > other_team_points:
                            sets_won += 1
                        elif team_points < other_team_points:
                            sets_lost += 1
                        else:
                            raise UserError(_(
                                "Match {match_name}:\n"
                                "Draw not allowed").format(
                                    match_name=match.display_name))
                    points_done += team_points
                    points_taken += other_team_points
                total_sets_won += sets_won
                if match_mode:
                    matches_points += match_mode.get_points(match)[team]

            team.sets_won = total_sets_won
            team.points_ratio = points_done / (points_taken or 1)
            team.matches_points = matches_points
