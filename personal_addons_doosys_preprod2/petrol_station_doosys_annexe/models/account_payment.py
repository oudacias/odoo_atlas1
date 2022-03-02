# coding: utf-8

import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    station_id = fields.Many2one('petrol.station', string="Station")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")
    date_recette = fields.Date(related="recette_id.date_recette")
    type_payement = fields.Char(string="Type de paiement")
    amount_rec = fields.Monetary(string="Amount", compute="_amount_rec",store=True)
    amount_diff = fields.Monetary(string="Montant rest", compute="_amount_rec",store=True)

    @api.constrains("move_line_ids","amount")
    def _amount_rec(self):
        for rec in self:
            amoun = 0
            for move_line_id in rec.move_line_ids:
                print("_amount_rec usf",move_line_id,move_line_id.matched_debit_ids)
                amoun += sum([matched_debit_id.amount for matched_debit_id in move_line_id.matched_debit_ids])
            if amoun:
                rec.amount_rec =   amoun
            else:
                rec.amount_rec = rec.amount


            rec.amount_diff = rec.amount - rec.amount_rec
