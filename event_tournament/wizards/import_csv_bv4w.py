#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import csv
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

COLUMNS = [
    "Timestamp",
    "Torneo",
    "Nome squadra",
    "Giocatore 1 (capitano referente)",  # 2x2
    "Data di nascita",
    "Cellulare capitano",
    "Email capitano",
    "Giocatore 2",
    "Data di nascita",
    "Giocatore 3 (opzionale)",
    "Data di nascita",
    "Giocatore 1 (capitano referente)",  # 3x3
    "Data di nascita",
    "Cellulare capitano",
    "Giocatore 2",
    "Data di nascita",
    "Giocatore 3",
    "Data di nascita",
    "Giocatore 4 (opzionale)",
    "Data di nascita",
    "Giocatore 5 (opzionale)",
    "Data di nascita",
    "Giocatore 1 (capitano referente)",  # 4x4
    "Data di nascita",
    "Tesserata/o FIPAV 2019",
    "Cellulare capitano",
    "Email capitano",
    "Giocatore 2",
    "Data di nascita",
    "Tesserata/o FIPAV 2019",
    "Giocatore 3",
    "Data di nascita",
    "Giocatore 4",
    "Data di nascita",
    "Tesserata/o FIPAV 2019",
    "Giocatore 5 (opzionale)",
    "Data di nascita",
    "Tesserata/o FIPAV 2019",
    "Giocatore 6 (opzionale)",
    "Data di nascita",
    "Tesserata/o FIPAV 2019",
    "Giocatore 7 (opzionale)",
    "Data di nascita",
    "Tesserata/o FIPAV 2019",
    "Giocatore 7 (opzionale)",
    "Data di nascita",
    "Tesserata/o FIPAV 2019",
    "Note aggiuntive (opzionale)",
    "Regolamento",
    "Email capitano",
    "Email Address",
    "Score",
]


def parse_team_line(values: list):
    # Strip all the values!
    values = list(map(str.strip, values))
    res = dict()
    common_fields = ["date_open", "tournament", "team_name"]
    common_values = values[: len(common_fields)]
    res.update(dict(zip(common_fields, common_values)))
    values = values[len(common_fields) :]

    common2_fields = ("notes", "rules", "email_cap", "email", "score")
    common2_values = values[-len(common2_fields) :]
    res.update(dict(zip(common2_fields, common2_values)))
    values = values[: -len(common2_fields)]

    values = list(filter(None, values))
    player_fields = ["name", "birthdate_date"]
    if res["tournament"].startswith("4x4"):
        player_fields += ["is_fipav"]

    players = list()
    captain_fields = player_fields + ["mobile"]
    captain_values = values[: len(captain_fields)]
    players.append(dict(zip(captain_fields, captain_values)))
    values = values[len(captain_fields) :]

    # Giocatore 3 in 4x4 has no 'fipav' field
    player_index = 2  # Captain is parsed already
    while values:
        curr_player_fields = player_fields.copy()
        if "is_fipav" in player_fields and player_index == 3:
            curr_player_fields.remove("is_fipav")
        player_values = values[: len(curr_player_fields)]
        players.append(dict(zip(curr_player_fields, player_values)))
        values = values[len(curr_player_fields) :]
        player_index += 1

    res.update(players=players)
    return res


class ImportCSVBV4W(models.TransientModel):
    _name = "event.tournament.import_csv_bv4w"
    _description = "Importing teams from BV4W in CSV format"

    data = fields.Binary("File", required=True)
    filename = fields.Char("File Name", required=True)

    def import_csv_bv4w(self):
        self.ensure_one()
        content = base64.decodebytes(self.data).decode()
        csv_lines = content.splitlines()
        csv_lines = list(csv.reader(csv_lines))
        team_lines = list()
        for line in csv_lines[1:]:
            team_lines.append(parse_team_line(line))

        team_model = self.env["event.tournament.team"]
        for team_line in team_lines:
            # We have to create every time so that registrations are always
            # updated and we can link existing ones if they join another team
            team_model.create(self.get_team_values(team_line))
        return True

    @api.model
    def get_team_values(self, team_dict):
        parsed_players = team_dict["players"]
        parsed_players[0]["email"] = team_dict["email"]
        tournament = self.env["event.tournament"].search(
            [("name", "=", team_dict["tournament"])]
        )
        if not tournament:
            raise UserError(
                _("No tournament found with name equal to '{csv_tourn_name}'").format(
                    csv_tourn_name=team_dict["tournament"]
                )
            )

        registrations = tournament.event_id.registration_ids

        players_values = list()
        date_open = datetime.strptime(team_dict["date_open"], "%m/%d/%Y %H:%M:%S")

        def same_player(registration, new_player_values):
            return (
                registration.name == new_player_values["name"]
                and registration.birthdate_date == new_player_values["birthdate_date"]
            )

        for parsed_player in parsed_players:
            player_values = parsed_player
            player_values["name"] = (
                player_values["name"].title().replace(" ", "")
            )  # Clean user data
            player_values["birthdate_date"] = datetime.strptime(
                player_values["birthdate_date"], "%m/%d/%Y"
            ).date()
            player_values["event_id"] = tournament.event_id.id
            player_values["date_open"] = date_open
            if "is_fipav" in parsed_player:
                not_fipav = parsed_player["is_fipav"].lower() == "no"
                player_values["is_fipav"] = not not_fipav
            existing_registration = registrations.filtered(
                lambda r: same_player(r, player_values)
            )
            if existing_registration:
                if len(existing_registration) > 1:
                    raise UserError(
                        _("Found multiple registrations with name {name}").format(
                            name=player_values["name"]
                        )
                    )
                existing_registration.update(player_values)
                players_values.append((4, existing_registration.id))
            else:
                players_values.append((0, 0, player_values))
        return {
            "name": team_dict["team_name"],
            "component_ids": players_values,
            "tournament_id": tournament.id,
            "notes": team_dict["notes"] or False,
        }
