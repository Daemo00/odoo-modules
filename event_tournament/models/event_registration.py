#  Copyright 2019 Simone Rubino <daemo00@gmail.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    tournament_team_ids = fields.Many2many(
        comodel_name='event.tournament.team',
        string="Teams")
    tournament_ids = fields.Many2many(
        comodel_name='event.tournament',
        compute='compute_tournaments',
        store=True)
    birthdate_date = fields.Date(
        string="Birthdate")
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')])
    mobile = fields.Char(
        string="Mobile")
    is_fipav = fields.Boolean(
        string="Is FIPAV")

    @api.onchange('partner_id')
    def _onchange_partner(self):
        res = super()._onchange_partner()
        if self.partner_id:
            contact_id = self.partner_id.address_get().get('contact', False)
            if contact_id:
                contact = self.env['res.partner'].browse(contact_id)
                self.gender = contact.gender or self.gender
                self.birthdate_date = \
                    contact.birthdate_date or self.birthdate_date
                self.mobile = contact.mobile or self.mobile
        return res

    @api.depends('tournament_team_ids')
    def compute_tournaments(self):
        for registration in self:
            registration.tournament_ids = \
                registration.tournament_team_ids.mapped('tournament_id')
