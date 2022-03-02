# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    magasin_code = fields.Char(related="station_id.magasin_code")