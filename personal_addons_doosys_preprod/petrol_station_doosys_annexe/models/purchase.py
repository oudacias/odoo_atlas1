# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    station_id = fields.Many2one('petrol.station', string="Station")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")