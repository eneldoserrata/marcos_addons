# -*- coding: utf-8 -*-
{
    'name': "Comprobantes fiscales RD",

    'summary': """
        Localizacion Para Republica Dominicana
        Implementacion de numeros de comprobantes fiscales""",

    'description': """
        Permite administrar y configurar comprobantes fiscales ademas de
        generar los reportes 606,607,608 y 609
    """,

    'author': "Marcos Organizador de Negocios SRL - Write by Eneldo Serrata",
    'website': "http://marcos.do",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization',
    'version': '3.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_invoice_change_currency',
                'web_sheet_full_width', 'marcos_api_tools','l10n_do'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/ncf_manager_security.xml',
        'wizard/account_invoice_cancel_view.xml',
        'wizard/update_rate_wizard_view.xml',
        'wizard/account_invoice_refund.xml',
        'views/shop_view.xml',
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/dgii_exterior_view.xml',
        'views/dgii_purchase_view.xml',
        'views/dgii_sale_view.xml',
        'views/dgii_cancel_view.xml',
        'views/res_view.xml',
        'data/setup_ncf.xml'
    ],
    'license': "Other proprietary",
}
