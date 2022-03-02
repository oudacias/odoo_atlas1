# -*- coding: utf-8 -*-
{
    'name': "Cendana Admin Theme",

    'summary': """
        This is a simple backend/admin style
        """,

    'src': """
        Long src of module's purpose
    """,

    'author': "Zamal A.H",
    'website': "http://www.cendana2000.com",

    'category': 'Themes',
    'version': '1.0',
    'license': 'LGPL-3',
    'support': 'zamalabdulhalim@gmail.com',
    'images': ['static/description/banner1.png'],

    'depends': ['web','cendana_custom_odoo_login'],

    # always loaded
    'data': [
        'view/custom_backend_style.xml',
    ],

    'installable' : True,
    'application' : True,

}