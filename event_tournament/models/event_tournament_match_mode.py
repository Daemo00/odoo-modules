#  Copyright 2019 ~ 2023 Simone Rubino <daemo00@gmail.com>
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
    win_points = fields.Integer(
        help="Points awarded to the teams that wins the match.",
    )
    lose_points = fields.Integer(
        help="Points awarded to the teams that do not win the match.",
    )


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
        stats = match.stats_ids
        for stat in stats:
            team = stat.team_id
            won_lost_sets = (won_sets, lost_sets) = (
                stat.won_sets_count,
                stat.lost_sets_count,
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

    def get_set_winners(self, set_):
        winner_teams = self.env["event.tournament.team"].browse()

        for team in set_.match_team_ids:
            results = set_.result_ids
            team_results = results.filtered(lambda result: result.team_id == team)
            other_teams_results = results - team_results
            set_done_points = sum(team_results.mapped("score"))
            set_taken_points = sum(other_teams_results.mapped("score"))
            if set_done_points > set_taken_points:
                winner_teams |= team
        return winner_teams

    def get_match_winners(self, match):
        winner_teams = self.env["event.tournament.team"].browse()
        max_won_sets = 0
        for stat in match.stats_ids:
            team = stat.team_id
            won_sets_count = stat.won_sets_count
            if won_sets_count == max_won_sets:
                winner_teams |= team
            elif won_sets_count > max_won_sets:
                winner_teams = team
                max_won_sets = won_sets_count
        return winner_teams
