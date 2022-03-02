# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, _

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    date_end = fields.Date('End Date', help="Ending valid for the pricelist item validation", compute="_date_end",store=True)
    updated  = fields.Boolean('Updated')

    @api.model
    def create(self, vals):
        rec = super(PricelistItem, self).create(vals)
        pricelist_id = self.env["product.pricelist.item"].search(
            [('pricelist_id', '=', rec.pricelist_id.id),('product_tmpl_id', '=', rec.product_tmpl_id.id), ('date_start', '<', rec.date_start)], order="date_start desc",
            limit=1)
        pricelist_id.write({
            "updated": not pricelist_id.updated
        })
        #pricelist_id.updated =  not pricelist_id.updated
        return rec

    @api.multi
    def write(self, vals):
        #res =  super(PricelistItem, self).write(vals)
        if vals.get("date_start") or vals.get("pricelist_id"):
            pricelist_id = self.env["product.pricelist.item"].search(
                [('pricelist_id', '=', self.pricelist_id.id),('product_tmpl_id', '=', self.product_tmpl_id.id), ('date_start', '<', self.date_start)], order="date_start desc",
                limit=1)
            pricelist_id.write({
                "updated":not pricelist_id.updated
            })


        return super(PricelistItem, self).write(vals)

    @api.multi
    @api.depends("pricelist_id","date_start","")
    def _update(self):
        for rec in self:
            pricelist_id = self.env["product.pricelist.item"].search([('pricelist_id','=',rec.pricelist_id.id),('product_tmpl_id', '=', rec.product_tmpl_id.id),('date_start','<',rec.date_start)], order="date_start desc", limit=1)
            print("pricelist_id :",pricelist_id.date_start)
           # pricelist_id.date_end = fields.Datetime.from_string(rec.date_start) - relativedelta(days=1)
            print("pricelist_id :", pricelist_id.date_start,pricelist_id.date_end)
            rec.updated = not rec.updated

    @api.model
    def update_date_end_prix_list(self):
        recs = self.search([])
        print("update_date_end_prix_list")
        for rec in recs:
            item_id = self.env["product.pricelist.item"].search([('pricelist_id','=',rec.pricelist_id.id),('product_tmpl_id', '=', rec.product_tmpl_id.id),('date_start','>',rec.date_start)], order="date_start asc", limit=1)
            if item_id:
                #rec.date_end = item_id.date_start+ relativdelta(days=3)
                rec.date_end = fields.Datetime.from_string(item_id.date_start) - relativedelta(days=1)
            else :
                if rec.date_start:

                 rec.date_end = fields.Datetime.from_string(rec.date_start) + timedelta(days=30)


    @api.multi
    @api.depends("pricelist_id","date_start","updated")
    def _date_end(self):
        for rec in self:

            item_id = self.env["product.pricelist.item"].search([('pricelist_id','=',rec.pricelist_id.id),('product_tmpl_id', '=', rec.product_tmpl_id.id),('date_start','>',rec.date_start)], order="date_start asc", limit=1)
            print("_date_end",rec.date_start,rec.date_end,item_id.date_start)
            if item_id:
                print("_date_end2", rec.date_start, rec.date_end, item_id.date_start)
                #rec.date_end = item_id.date_start+ relativedelta(days=3)
                rec.date_end = fields.Datetime.from_string(item_id.date_start) - relativedelta(days=1)
                print(rec.date_end)
            else:
                if rec.date_start:
                    item_id = self.env["product.pricelist.item"].search(
                        [('pricelist_id', '=', rec.pricelist_id.id),('product_tmpl_id', '=', rec.product_tmpl_id.id), ('date_start', '>', rec.date_start)],
                        order="date_start asc", limit=1)

                    rec.date_end = fields.Datetime.from_string(rec.date_start) + timedelta(days=60)

