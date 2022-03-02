# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    station_id  = fields.Many2one('petrol.station' , string="Station")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")

class StockLocation(models.Model):
    _inherit = 'stock.location'

    station_id  = fields.Many2one('petrol.station' , string="Station")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")




