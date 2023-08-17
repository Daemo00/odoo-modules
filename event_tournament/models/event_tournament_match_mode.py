#  Copyright 2019 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import Counter

from odoo import _, api, fields, models
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
    win_set_points = fields.Integer(
        string="Points for winning a set",
    )
    win_tie_break_points = fields.Integer(
        string="Points for winning the tie break",
    )
    win_set_break_points = fields.Integer(
        string="Break for winning a set",
    )
    tie_break_number = fields.Integer(
        compute="_compute_tie_break_number",
        store=True,
        readonly=False,
    )

    @api.depends(
        "result_ids.won_sets",
        "result_ids.lost_sets",
    )
    def _compute_tie_break_number(self):
        for mode in self:
            results = mode.result_ids
            max_played_sets = max(r.won_sets + r.lost_sets for r in results)
            tie_break_set_number = int(max_played_sets / 2) + 1
            mode.tie_break_number = tie_break_set_number

    def get_points(self, match):
        """
        Get a dictionary storing the points of each team involved in `match`.

        :return: A dictionary mapping teams to how many points they obtained
        """
        self.ensure_one()
        if match.state == "done":
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
        else:
            tournament_points = {}
        return tournament_points

    def get_set_winners(self, set_):
        self.ensure_one()
        match = set_.match_id
        if match.state == "done":
            # Might be substituted by something like set.team_stats
            team_points_dict = {
                result.team_id: result.score for result in set_.result_ids
            }

            points = sorted(team_points_dict.values())
            max_points = points[-1]
            other_points = sorted([score for score in points if score != max_points])
            if not other_points:
                raise UserError(
                    _(
                        "Set %(set)s not valid:\n" "Ties are not allowed",
                        set=set_.display_name,
                    )
                )
            second_max_points = other_points[-1]

            win_set_points = (
                self.win_set_points
                if not set_.is_tie_break
                else self.win_tie_break_points
            )
            win_break_points = self.win_set_break_points
            if max_points < win_set_points:
                raise UserError(
                    _(
                        "Set %(set)s not valid:\n"
                        "At least one team must reach %(win_set_points)d",
                        set=set_.display_name,
                        win_set_points=win_set_points,
                    )
                )
            else:
                break_points = max_points - second_max_points
                if (
                    # 25 - 24 is not valid for volleyball
                    max_points == win_set_points
                    and break_points < win_break_points
                ) or (
                    # 33 - 30 is not valid for volleyball
                    max_points > win_set_points
                    and break_points != win_break_points
                ):
                    raise UserError(
                        _(
                            "Set %(set)s not valid:\n"
                            "There must be exactly %(win_break_points)d points "
                            "between the winner and the second team.",
                            set=set_.display_name,
                            win_break_points=win_break_points,
                        )
                    )

            winner_teams = filter(
                lambda t: team_points_dict[t] == max_points, team_points_dict.keys()
            )
            winner_teams_ids = [t.id for t in winner_teams]
            winner_teams = self.env["event.tournament.team"].browse(winner_teams_ids)
        else:
            winner_teams = self.env["event.tournament.team"].browse()
        return winner_teams

    def get_match_winners(self, match):
        self.ensure_one()
        winner_teams = self.env["event.tournament.team"].browse()
        if match.state == "done":
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
