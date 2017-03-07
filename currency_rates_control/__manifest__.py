# -*- coding: utf-8 -*-
{
    'name': "currency_check",

    'summary': """
        Short summary of the module's purpose""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Gustavo Valverde",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module
    # /module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'ncf_manager'],

    # always loaded
    'data': [
        'wizard/update_rate_wizard_view.xml',
        'views/account_invoice_view.xml',
    ],
}
