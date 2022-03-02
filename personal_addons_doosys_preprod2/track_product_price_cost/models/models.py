# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class TrackPriceCostProduct(models.Model):
    _name = 'track.product.price.cost'      
    name = fields.Char(string="Nom")
    product_id=fields.Many2one('product.product', "Produit")
    old_price = fields.Float(
        'Ancien prix de vente',
        digits=dp.get_precision('Product Price'))
    new_price = fields.Float(
        'Nouveau   prix de vente',
        digits=dp.get_precision('Product Price'))
    old_cost = fields.Float(
        'Ancien coût',
        digits=dp.get_precision('Product Price'))
    new_cost = fields.Float(
        'Nouveau coût',
        digits=dp.get_precision('Product Price'))

class ProductPruduct(models.Model):
    _inherit='product.product'
    track_price_cost_ids=fields.One2many('track.product.price.cost','product_id', "tracking prix de vente et coût")
    @api.multi
    def write(self, vals):
        if 'lst_price' in vals or 'standard_price' in vals :
            if 'lst_price' in vals:
                new_price= vals['lst_price']
            else:
                new_price= self.lst_price
            old_price=self.lst_price
            if 'standard_price' in vals:
                new_cost= vals['standard_price']
            else:
                new_cost= self.standard_price
            old_cost=self.standard_price
            vals_h={'product_id':self.id,
                  'old_price':old_price,
                  'new_price':new_price,
                  'old_cost':old_cost,
                  'new_cost':new_cost,
                }
            self.env['track.product.price.cost'].create(vals_h)
        res = super(ProductPruduct, self).write(vals)
        return res

   