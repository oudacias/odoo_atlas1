# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError



class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    station_id = fields.Many2one('petrol.station', string="Station",compute="_station_id")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")

    magasin_code = fields.Char(related="station_id.magasin_code")


    @api.one
    @api.depends("location_dest_id")
    def _station_id(self):
        if self.location_dest_id:
            self.station_id = self.location_dest_id.station_id
