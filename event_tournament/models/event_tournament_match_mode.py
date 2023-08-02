#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import Counter

from odoo import _, fields, models
from odoo.exceptions import UserError


class EventTournamentMatchModeLine(models.Model):
    _name = "event.tournament.match.mode.result"
    _description = "Match mode result"

    mode_id = fields.Many2one(comodel_name="event.tournament.match.mode")
    won_sets = fields.Integer()
    lost_sets = fields.Integer()
    win_points = fields.Integer()
    lose_points = fields.Integer()


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
            won_lost_sets = (won_sets, lost_sets) = (
                sets_info["won_sets"],
                sets_info["lost_sets"],
            )

            for res in self.result_ids:
                if won_lost_sets == (res.won_sets, res.lost_sets):
                    tournament_points[team] = res.win_points
                    break
                if won_lost_sets == (res.lost_sets, res.won_sets):
                    tournament_points[team] = res.lose_points
                    break
            else:
                raise UserError(
                    _(
                        "Match {match_name} not valid:\n"
                        "Result {won_sets} - {lost_sets} not expected "
                        "for match mode {match_mode}."
                    ).format(
                        match_name=match.display_name,
                        won_sets=won_sets,
                        lost_sets=lost_sets,
                        match_mode=self.display_name,
                    )
                )
        return tournament_points
