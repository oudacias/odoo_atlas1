# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):

    _inherit = "product.template"

    @api.multi
    def _set_template_price(self):
        if self._context.get('uom'):
            for template in self:
                value = self.env['product.uom'].browse(self._context['uom'])._compute_price(template.price,
                                                                                            template.uom_id)

                template.write({'list_price': value})
        else:
            if not self.list_price:
             self.write({'list_price': self.price})
