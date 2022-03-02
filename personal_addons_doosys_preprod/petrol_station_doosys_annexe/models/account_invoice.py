# -*- coding: utf-8 -*-



from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    station_id = fields.Many2one('petrol.station', string="Station")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")
    date_recette = fields.Date(related="recette_id.date_recette")
    client_name = fields.Char(related='partner_id.name')
    type_payement = fields.Char(string="Type de paiement")