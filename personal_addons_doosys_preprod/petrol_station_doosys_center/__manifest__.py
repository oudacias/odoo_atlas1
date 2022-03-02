# -*- coding: utf-8 -*-
{
    'name': "petrol_station_doosys_central",

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
    'depends': ['base','petrol_station_doosys','petrol_station_doosys_annexe'],

    # always loaded
    'data': [
        "data/cron.xml",
        "data/mail.xml",
        "views/configuration.xml",
        "views/station_recette.xml",
        "views/sale_order.xml"


    ],
    # only loaded in demonstration mode
#     'demo': [
#         'demo/demo.xml',
#     ],
}