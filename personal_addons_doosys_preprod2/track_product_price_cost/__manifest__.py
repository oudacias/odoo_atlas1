# -*- coding: utf-8 -*-
{
    'name': "track_product_price_cost",

    'summary': """
        Track Price Cost price""",

    'description': """
         Track Price Cost price"
    """,

    'author': "YOUSSEF NOUNI, DOOSYS",
    'website': "http://www.yourcompany.com",


    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','mail','product'],

    'data': [

        'security/ir.model.access.csv',

        'views/product_product_view.xml',
    ],

}