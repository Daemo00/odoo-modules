#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import Counter

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventTournamentMatchModeLine(models.Model):
    _name = 'event.tournament.match.mode.result'
    _description = 'Match mode result'

    mode_id = fields.Many2one(
        comodel_name='event.tournament.match.mode')
    sets_won = fields.Integer()
    sets_lost = fields.Integer()
    points_win = fields.Integer()
    points_lose = fields.Integer()


class EventTournamentMatchMode(models.Model):
    _name = 'event.tournament.match.mode'
    _description = 'Match mode'

    name = fields.Char()
    result_ids = fields.One2many(
        comodel_name='event.tournament.match.mode.result',
        inverse_name='mode_id')

    @api.multi
    def get_points(self, match):
        self.ensure_one()
        sets_played, team_sets_won = match.get_sets_info()
        team_points = dict.fromkeys(match.team_ids, 0)
        for team, sets_won in team_sets_won.items():
            sets_lost = sets_played - sets_won
            for res in self.result_ids:
                if res.sets_won == sets_won and res.sets_lost == sets_lost:
                    team_points[team] = res.points_win
                    break
                if res.sets_won == sets_lost and res.sets_lost == sets_won:
                    team_points[team] = res.points_lose
                    break
            else:
                raise UserError(
                    _("Match {match_name}:\n"
                      "Result {sets_won} - {sets_lost} not expected")
                    .format(
                        match_name=match.display_name,
                        sets_won=sets_won,
                        sets_lost=sets_lost))
        return team_points
