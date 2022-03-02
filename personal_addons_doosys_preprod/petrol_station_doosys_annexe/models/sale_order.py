# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    station_id = fields.Many2one('petrol.station', string="Station")


    type_payement = fields.Char(string="Type de paiement")
    client_name = fields.Char(related='partner_id.name')

    

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.type_payement:
            invoice_vals['type_payement'] = self.type_payement
        if self.station_id:
            invoice_vals['station_id'] = self.station_id.id
        if self.recette_id:
            invoice_vals['recette_id'] = self.recette_id.id
        return invoice_vals