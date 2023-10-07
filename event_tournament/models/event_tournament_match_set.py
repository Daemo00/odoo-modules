#  Copyright 2020 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Command
from odoo.models import NewId


class EventTournamentMatchSet(models.Model):
    _name = "event.tournament.match.set"
    _description = "Set of a Tournament match"

    name = fields.Char(
        required=True,
    )
    match_id = fields.Many2one(
        comodel_name="event.tournament.match", required=True, ondelete="cascade"
    )
    match_team_ids = fields.Many2many(
        related="match_id.team_ids",
        relation="event_tournament_set_team_rel",
        column1="set_id",
        column2="team_id",
        readonly=True,
        store=True,
    )
    result_ids = fields.One2many(
        comodel_name="event.tournament.match.set.result",
        inverse_name="set_id",
        compute="_compute_result_ids",
        store=True,
        readonly=False,
    )
    winner_team_id = fields.Many2many(
        comodel_name="event.tournament.team",
        relation="event_tournament_set_winner_team_rel",
        column1="set_id",
        column2="team_id",
        compute="_compute_winner_team_id",
        store=True,
        help="Only computed on done matches.",
    )
    is_tie_break = fields.Boolean(
        compute="_compute_is_tie_break",
        store=True,
    )

    @api.depends(
        "match_id.match_mode_id.tie_break_number",
    )
    def _compute_is_tie_break(self):
        for set_ in self:
            match = set_.match_id
            match_mode = match.match_mode_id
            tie_break_number = match_mode.tie_break_number
            sets = match.set_ids
            is_tie_break = (
                len(sets) >= tie_break_number and sets[tie_break_number - 1] == set_
            )
            set_.is_tie_break = is_tie_break

    @api.depends(
        "match_id.match_mode_id.win_set_points",
        "match_id.match_mode_id.win_set_break_points",
        "match_id.match_mode_id.win_tie_break_points",
        "match_id.state",
        "is_tie_break",
        "result_ids.score",
        "match_team_ids",
    )
    def _compute_winner_team_id(self):
        for set_ in self:
            match = set_.match_id
            if match.state == "done":
                match_mode = match.match_mode_id
                winner_team = match_mode.get_set_winner(set_)
            else:
                winner_team = self.env["event.tournament.team"].browse()
            set_.winner_team_id = winner_team

    @api.depends(
        "match_id.team_ids",
    )
    def _compute_result_ids(self):
        for set_ in self:
            match = set_.match_id
            needing_result_teams = match.team_ids
            existing_results = set_.result_ids
            results_command = []
            if existing_results:
                for existing_result in existing_results:
                    team = existing_result.team_id
                    if team not in match.team_ids:
                        # Otherwise when a team is removed from the match,
                        # the result cannot be deleted
                        # (tries to empty its set_id before deleting it)
                        if not isinstance(match.id, NewId):
                            # A team has been removed: remove its results
                            results_command.append(
                                Command.delete(existing_result.id),
                            )
                    else:
                        needing_result_teams -= team

            results_command.extend(
                [
                    Command.create(
                        {
                            "team_id": team.id,
                        }
                    )
                    for team in needing_result_teams
                ]
            )
            set_.result_ids = results_command

    def name_get(self):
        return [
            (
                set_.id,
                f"{set_.name}: "
                + " - ".join(str(result.score) for result in set_.result_ids),
            )
            for set_ in self
        ]
