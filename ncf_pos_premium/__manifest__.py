# -*- coding: utf-8 -*-

{
    'name': "NCF POS Premium",

    'summary': """
        Incorpora funcionalidades extras el POS de odoo
        """,

    'description': """
-Sesiones sincronizadas
-Pantalla de cocina o despacho
-Notas de crédito y mucho más...
    """,
    'author': "Marcos Organizador de Negocios SRL - Write by Eneldo Serrata",
    'website': "http://marcos.do",
    'category': 'POS',
    'version': '10.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'bus', 'stock', 'point_of_sale', 'pos_restaurant', 'ncf_manager', 'ipf_manager',
                'queue_job'],
    "external_dependencies": {"python": [], "bin": []},
    # always loaded
    'data': [
        'wizard/fix_payment_mistake_wizard.xml',
        'security/ir.model.access.csv',
        'views/pos_view.xml',
        'views/pos_sesion_view.xml',
        'views/pos_config_view.xml',
        'data/data.xml',
        'views/sale_order_view.xml',
        'views/res_partner_view.xml',
        'views/res_users_view.xml',
        'views/restaurant.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/action_pad.xml',
        'static/src/xml/client.xml',
        'static/src/xml/payment.xml',
        'static/src/xml/popup.xml',
        'static/src/xml/pos_order.xml',
        'static/src/xml/pos_orders.xml',
        'static/src/xml/pos_ticket.xml',
        'static/src/xml/bus.xml',
        'static/src/xml/restaurant.xml',
        'static/src/xml/sale_order.xml',
        'static/src/xml/lock_screen.xml',
        'static/src/xml/delivery_screen.xml',
    ],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,

    "auto_install": False,
    "installable": True,
    'price': 2000,
    'currency': 'EUR',
    'license': 'Other proprietary'
}
