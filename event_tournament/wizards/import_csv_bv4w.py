#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import csv

from odoo import api, fields, models

COLUMNS_COMMON = [
    'Timestamp',
    'Torneo',
    'Nome squadra',
    'Giocatore 1 (capitano referente)',  # 2x2
    'Data di nascita',
    'Cellulare capitano',
    'Email capitano',
    'Giocatore 2',
    'Data di nascita',
    'Giocatore 3 (opzionale)',
    'Data di nascita',
    'Giocatore 1 (capitano referente)',  # 3x3
    'Data di nascita',
    'Cellulare capitano',
    'Giocatore 2',
    'Data di nascita',
    'Giocatore 3',
    'Data di nascita',
    'Giocatore 4 (opzionale)',
    'Data di nascita',
    'Giocatore 5 (opzionale)',
    'Data di nascita',
    'Giocatore 1 (capitano referente)',  # 4x4
    'Data di nascita',
    'Tesserata/o FIPAV 2019',
    'Cellulare capitano',
    'Email capitano',
    'Giocatore 2',
    'Data di nascita',
    'Tesserata/o FIPAV 2019',
    'Giocatore 3',
    'Data di nascita',
    'Giocatore 4',
    'Data di nascita',
    'Tesserata/o FIPAV 2019',
    'Giocatore 5 (opzionale)',
    'Data di nascita',
    'Tesserata/o FIPAV 2019',
    'Giocatore 6 (opzionale)',
    'Data di nascita',
    'Tesserata/o FIPAV 2019',
    'Giocatore 7 (opzionale)',
    'Data di nascita',
    'Tesserata/o FIPAV 2019',
    'Giocatore 7 (opzionale)',
    'Data di nascita',
    'Tesserata/o FIPAV 2019',
    'Note aggiuntive (opzionale)',
    'Regolamento',
    'Email capitano',
    'Email Address',
    'Score']


def parse_team_line(values: list):
    res = dict()
    common_fields = ['timestamp', 'tournament', 'team_name']
    common_values = values[:len(common_fields)]
    res.update(dict(zip(common_fields, common_values)))
    values = values[len(common_fields):]

    common2_fields = ('notes', 'rules', 'email_cap', 'email', 'score')
    common2_values = values[-len(common2_fields):]
    res.update(dict(zip(common2_fields, common2_values)))
    values = values[:-len(common2_fields)]

    values = list(filter(None, values))
    player_fields = ['player_name', 'date_birth']
    if res['tournament'].startswith('4x4'):
        player_fields += ['fipav']

    players = list()
    captain_fields = player_fields + ['mobile']
    captain_values = values[:len(captain_fields)]
    players.append(dict(zip(captain_fields, captain_values)))
    values = values[len(captain_fields):]

    while values:
        player_values = values[:len(player_fields)]
        players.append(dict(zip(player_fields, player_values)))
        values = values[len(player_fields):]

    res.update(players=players)
    return res


class ImportCSVBV4W (models.TransientModel):
    _name = 'event.tournament.import_csv_bv4w'

    data = fields.Binary('File', required=True)
    filename = fields.Char('File Name', required=True)

    @api.multi
    def import_csv_bv4w(self):
        self.ensure_one()
        content = base64.decodebytes(self.data).decode()
        csv_lines = content.splitlines()
        csv_lines = list(csv.reader(csv_lines))
        team_lines = list()
        for line in csv_lines[1:]:
            team_lines.append(parse_team_line(line))
        return True

    @api.multi
    def parse_team_line(self, columns):
        self.ensure_one()
