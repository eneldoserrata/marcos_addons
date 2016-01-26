{
    "name": "pos_orders_control",
    "category": 'point_of_sale',
    "summary": """
        Dominican republic pos order control
       """,
    "sequence": 1,

    "depends": ['base', 'point_of_sale', 'ncf_pos'],
    "data": [
        'views/pos_orders_view.xml',
    ],

    'qweb': [
        'static/src/xml/*.xml',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
