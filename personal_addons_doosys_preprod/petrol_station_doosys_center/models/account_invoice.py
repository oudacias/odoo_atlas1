# -*- coding: utf-8 -*-



from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"


    magasin_code = fields.Char(related="station_id.magasin_code")