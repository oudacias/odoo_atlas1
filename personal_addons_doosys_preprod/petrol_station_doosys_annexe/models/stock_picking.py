# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Picking(models.Model):
    _inherit = "stock.picking"

    station_id = fields.Many2one('petrol.station', string="Station", compute="_station_id")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")

class StockMove(models.Model):
    _inherit = 'stock.move'

    station_id  = fields.Many2one('petrol.station' , string="Station")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")



class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    station_id = fields.Many2one(related="move_id.station_id")
    recette_id = fields.Many2one(related="move_id.recette_id")
    date_recette = fields.Date(related="recette_id.date_recette")
    n_bl = fields.Char("N°BL")



    @api.one
    @api.depends("location_dest_id")
    def _station_id(self):
        if self.location_dest_id:
            self.station_id = self.location_dest_id.station_id
