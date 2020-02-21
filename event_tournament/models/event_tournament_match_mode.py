#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import Counter

from odoo import _, fields, models
from odoo.exceptions import UserError


class EventTournamentMatchModeLine(models.Model):
    _name = "event.tournament.match.mode.result"
    _description = "Match mode result"

    mode_id = fields.Many2one(comodel_name="event.tournament.match.mode")
    sets_won = fields.Integer()
    sets_lost = fields.Integer()
    points_win = fields.Integer()
    points_lose = fields.Integer()


class EventTournamentMatchMode(models.Model):
    _name = "event.tournament.match.mode"
    _description = "Match mode"

    name = fields.Char()
    result_ids = fields.One2many(
        comodel_name="event.tournament.match.mode.result", inverse_name="mode_id"
    )

    def get_points(self, match):
        """
        Get a dictionary storing the points of each team involved in `match`.

        :return: A dictionary mapping teams to how many points they obtained
        """
        self.ensure_one()
        tournament_points = Counter(match.team_ids)
        for team, sets_info in match.get_sets_info().items():
            sets_lost, sets_won, points_done, points_taken = sets_info
            for res in self.result_ids:
                if res.sets_won == sets_won and res.sets_lost == sets_lost:
                    tournament_points[team] = res.points_win
                    break
                if res.sets_won == sets_lost and res.sets_lost == sets_won:
                    tournament_points[team] = res.points_lose
                    break
            else:
                raise UserError(
                    _(
                        "Match {match_name} not valid:\n"
                        "Result {sets_won} - {sets_lost} not expected "
                        "for match mode {match_mode}."
                    ).format(
                        match_name=match.display_name,
                        sets_won=sets_won,
                        sets_lost=sets_lost,
                        match_mode=self.display_name,
                    )
                )
        return tournament_points
