#  Copyright 2020 ~ 2023 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EventTournamentMatchSetResult(models.Model):
    _name = "event.tournament.match.set.result"
    _description = "Result of a Set of a Tournament match"

    tournament_id = fields.Many2one(
        related="match_id.tournament_id",
    )
    court_id = fields.Many2one(
        related="match_id.court_id",
    )
    match_mode_id = fields.Many2one(
        related="match_id.match_mode_id",
    )
    match_id = fields.Many2one(
        related="set_id.match_id",
    )
    set_id = fields.Many2one(
        comodel_name="event.tournament.match.set", required=True, ondelete="cascade"
    )
    set_team_ids = fields.Many2many(
        related="set_id.match_team_ids",
        relation="event_tournament_result_team_rel",
        column1="result_id",
        column2="team_id",
        readonly=True,
        store=True,
        string="Match Teams",
    )
    team_id = fields.Many2one(
        comodel_name="event.tournament.team",
        required=True,
        ondelete="restrict",
        domain="[('id', 'in', set_team_ids)]",
    )
    score = fields.Integer()

    _sql_constraints = [
        (
            "unique_set_team",
            "UNIQUE(team_id, set_id)",
            "A team can only have one score in each set.",
        ),
    ]

    def name_get(self):
        names = [
            (
                result.id,
                f"{result.team_id.name}: {result.score}",
            )
            for result in self
        ]
        return names
