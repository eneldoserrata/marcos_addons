# -*- coding: utf-8 -*-
{
    'name': "ncf_cjc",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'hr', 'hr_expense', 'ncf_manager'],

    # always loaded
    'data': [
        'security/ncf_cjc_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/account_view.xml',
        'views/hr_view.xml',
        'views/templates.xml',
        'views/cjc_concept.xml',
        'wizard/cjc_wizard_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}