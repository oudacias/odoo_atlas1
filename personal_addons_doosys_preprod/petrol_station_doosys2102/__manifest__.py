# -*- coding: utf-8 -*-
{
    'name': "petrol_station_doosys",

    'summary': """
        Petrol Station Management Systems""",

    'description': """
        Petrol Station Management Systems
    """,

    'author': "YOUSSEF NOUNI, DOOSYS",
    'website': "http://www.yourcompany.comm",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','sale','track_product_price_cost','purchase','sale_automatic_workflow_payment_mode','account_payment_mode'],

    # always loaded
    'data': [

         'security/goup_security.xml',
        'security/ir.model.access.csv',
        'views/report2.xml',
        'views/configuration.xml',
        'views/station_recette.xml',
        'views/res_users_view.xml',
        'data/precision.xml',
        'data/cron1.xml',
        
    ],
    # only loaded in demonstration mode
#     'demo': [
#         'demo/demo.xml',
#     ],
}