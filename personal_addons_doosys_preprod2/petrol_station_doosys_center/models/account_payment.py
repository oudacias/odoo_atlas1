# coding: utf-8

import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    station_id = fields.Many2one('petrol.station', string="Station")
    magasin_code = fields.Char(related="station_id.magasin_code")

    client_name = fields.Char(related='partner_id.name')
    invoice_id = fields.Many2one('account.invoice', compute="_invoice_id" , string="Facture")
    invoice_name = fields.Char(related="invoice_id.number", string="Numero")



    @api.one
    @api.depends("invoice_ids")
    def _invoice_id(self):
        if len(self.invoice_ids) > 0:
            self.invoice_id = self.invoice_ids[0]
