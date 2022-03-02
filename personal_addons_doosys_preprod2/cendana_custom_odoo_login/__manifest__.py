# -*- coding: utf-8 -*-
{
    'name': "Cendana Custom Odoo Login",

    'summary': """
        This is a simple app to custome/modified default odoo login page for v10 and v11
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
    'images': ['static/description/icon.png'],

    'depends': ['base'],

    # always loaded
    'data': [
        'templates/cendana_custom_login_template.xml',
    ],

    'installable' : True,
    'application' : True,

}