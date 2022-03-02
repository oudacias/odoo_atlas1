# -*- coding: utf-8 -*-
{
    'name': "synchro sap doosys ApI ",

    'summary': """
        """,

    'description': """
       
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

        'security/ir.model.access.csv',
        'views/sap_objects.xml',
        'views/recette_report.xml',
        'data/data.xml',
        'wizard/lance_synch.xml'
    ],
    # only loaded in demonstration mode
#     'demo': [
#         'demo/demo.xml',
#     ],
}