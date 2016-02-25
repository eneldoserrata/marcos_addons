# -*- coding: utf-8 -*-

{
    'name': 'Dominican Republic - Accounting Custom',
    'version': '1.0',
    'category': 'Localization/Account Charts',
    'description': """
This is the base module to manage the accounting chart for Dominican Republic.
==============================================================================

* Chart of Accounts.
* The Tax Code Chart for Domincan Republic
* The main taxes used in Domincan Republic
* Fiscal position for local """,
    'author': 'Eneldo Serrata - Marcos Organizador de Negocios, SRL.',
    'website': 'http://marcos.do',
    'depends': ['account', 'base_iban','l10n_do_postal_code'],
    'data': [
        #Base template 01
        'data/template01/account_chart_template.xml',
        'data/template01/account.account.template.csv',
        'data/template01/set_account_on_chart_template.xml',
        'data/template01/account_account_tag.xml',
        'data/template01/account.tax.template.csv',
        'data/template01/l10n_do_base_data.xml',
        'data/template01/account.fiscal.position.template.csv',
        'data/template01/account.fiscal.position.tax.template.csv',
        'data/template01/ir.sequence.csv',
        # 'data/template01/account_chart_template.yml',

        # template 02
        'data/template02/account_chart_template.xml',
        'data/template02/account.account.template.csv',
        'data/template02/set_account_on_chart_template.xml',
        # 'data/template02/account_chart_template.yml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
