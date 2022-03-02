# -*- coding: utf-8 -*-
{
    'name': "petrol_station_doosys_annexe",

    'summary': """
        Petrol Station Management System annexe""",

    'description': """
        Petrol Station Management System annexe
    """,

    'author': "YOUSSEF ALLAFKIH, DOOSYS",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','petrol_station_doosys'],

    # always loaded
    'data': [
         "views/stock.xml",
         "views/petrol_station_reservoir.xml",
         "views/stock_picking.xml",
        "views/sale_order.xml",
        "views/account_invoice.xml",
        "views/purchase.xml",
        "views/account_payment_view.xml",
        "views/res_partner.xml"

    ],
    # only loaded in demonstration mode
#     'demo': [
#         'demo/demo.xml',
#     ],
}