#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

COLUMNS_COMMON = [
    'Timestamp',
    'Torneo',
    'Nome squadra',
    # 2x2
    'Giocatore 1 (capitano referente)',
    'Data di nascita',
    'Cellulare capitano',
    'Email capitano',
    'Giocatore 2',
    'Data di nascita',
    'Giocatore 3 (opzionale)',
    'Data di nascita',
    # 3x3
    'Giocatore 1 (capitano referente)',
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
    # 4x4
    'Giocatore 1 (capitano referente)',
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


class ImportCSVBV4W (models.TransientModel):
    _name = 'event.tournament.import_csv_bv4w'

    data = fields.Binary('File', required=True)
    filename = fields.Char('File Name', required=True)

    @api.multi
    def import_csv_bv4w(self):
        self.ensure_one()
        return True
