#  Copyright 2020 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EventTournamentMatchTeamStats(models.Model):
    _name = "event.tournament.match.team_stats"
    _description = "Team stats for a match"

    match_id = fields.Many2one(
        comodel_name="event.tournament.match",
        ondelete="cascade",
        required=True,
    )
    team_id = fields.Many2one(
        comodel_name="event.tournament.team",
        ondelete="cascade",
        required=True,
    )

    lost_set_ids = fields.Many2many(
        comodel_name="event.tournament.match.set",
        relation="event_tournament_match_team_stats_lost_set_rel",
        string="Lost Sets",
        compute="_compute_sets",
        store=True,
    )
    lost_sets_count = fields.Integer(
        compute="_compute_sets",
        store=True,
    )

    won_set_ids = fields.Many2many(
        comodel_name="event.tournament.match.set",
        relation="event_tournament_match_team_stats_won_set_rel",
        string="Won Sets",
        compute="_compute_sets",
        store=True,
    )
    won_sets_count = fields.Integer(
        compute="_compute_sets",
        store=True,
    )

    done_points = fields.Integer(
        compute="_compute_points",
        store=True,
    )
    taken_points = fields.Integer(
        compute="_compute_points",
        store=True,
    )

    sets_ratio = fields.Float(compute="_compute_sets_ratio", store=True, digits=(16, 5))
    points_ratio = fields.Float(
        compute="_compute_points_ratio", store=True, digits=(16, 5)
    )

    tournament_points = fields.Integer(
        compute="_compute_tournament_points",
        help="Only computed on done matches.",
        store=True,
    )

    @api.model
    def create_from_matches(self, matches):
        stats = self.create(
            [
                {
                    "match_id": match.id,
                    "team_id": team.id,
                }
                for match in matches
                for team in match.team_ids
            ]
        )
        return stats

    @api.depends(
        "match_id.set_ids.result_ids.score",
    )
    def _compute_points(self):
        for stat in self:
            team = stat.team_id
            match = stat.match_id

            sets = match.set_ids
            results = sets.result_ids
            match_points = sum(results.mapped("score"))

            team_results = results.filtered(lambda result: result.team_id == team)
            team_points = sum(team_results.mapped("score"))

            stat.done_points = team_points
            stat.taken_points = match_points - team_points

    @api.depends(
        "match_id.state",
        "match_id.match_mode_id.result_ids.won_sets",
        "match_id.match_mode_id.result_ids.lost_sets",
        "match_id.match_mode_id.result_ids.win_points",
        "match_id.match_mode_id.result_ids.lose_points",
        "match_id.stats_ids.won_sets_count",
        "match_id.stats_ids.lost_sets_count",
        "team_id",
    )
    def _compute_tournament_points(self):
        for stat in self:
            match = stat.match_id
            tournament_points = 0
            if match.state == "done":
                team = stat.team_id
                match_mode = match.match_mode_id
                if match_mode:
                    match_points = match_mode.get_points(match)
                    tournament_points = match_points.get(team, 0)

            stat.tournament_points = tournament_points

    @api.depends(
        "match_id.state",
        "team_id",
        "match_id.set_ids.winner_team_id",
    )
    def _compute_sets(self):
        set_model = self.env["event.tournament.match.set"]
        for stat in self:
            match = stat.match_id
            team = stat.team_id

            lost_sets = won_sets = set_model.browse()
            if match.state == "done":
                played_sets = match.set_ids.filtered(
                    lambda s: sum(s.result_ids.mapped("score"), 0)
                )
                for set_ in played_sets:
                    set_winner = set_.winner_team_id
                    if team == set_winner:
                        won_sets |= set_
                    else:
                        lost_sets |= set_

            stat.won_set_ids = won_sets
            stat.won_sets_count = len(won_sets)
            stat.lost_set_ids = lost_sets
            stat.lost_sets_count = len(lost_sets)

    @api.model
    def calculate_ratio(self, won, lost):
        return won / (lost or 0.1)

    def get_points_ratio(self):
        done_points = sum(self.mapped("done_points"))
        taken_points = sum(self.mapped("taken_points"))
        points_ratio = self.calculate_ratio(done_points, taken_points)
        return points_ratio

    def get_sets_ratio(self):
        won_sets_count = sum(self.mapped("won_sets_count"))
        lost_sets_count = sum(self.mapped("lost_sets_count"))
        sets_ratio = self.calculate_ratio(won_sets_count, lost_sets_count)
        return sets_ratio

    @api.depends(
        "done_points",
        "taken_points",
    )
    def _compute_points_ratio(self):
        for stat in self:
            stat.points_ratio = stat.get_points_ratio()

    @api.depends(
        "lost_sets_count",
        "won_sets_count",
    )
    def _compute_sets_ratio(self):
        for stat in self:
            stat.sets_ratio = stat.get_sets_ratio()
