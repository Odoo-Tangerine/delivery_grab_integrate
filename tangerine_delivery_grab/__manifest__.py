# -*- coding: utf-8 -*-
{
    'name': 'Grab Express Shipping',
    'summary': """GrabExpress APIs will allow shippers to easily place, cancel, get quotes, and track orders via simple integration for delivery in Odoo.""",
    'description': """
        GrabExpress APIs will allow shippers to easily place, cancel, get quotes, and track orders via simple integration for delivery in Odoo.
    """,
    'author': "Long Duong Nhat",
    'category': 'Inventory/Delivery',
    'version': '17.0.1.0',
    'depends': [
        'mail',
        'sale_management',
        'contacts',
        'stock_delivery',
        'stock',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/delivery_grab_data.xml',
        'data/grab_routes_api_data.xml',
        'data/ir_cron.xml',
        'data/grab_status_data.xml',
        'data/res_partner_data.xml',
        'wizard/choose_delivery_carrier_wizard_views.xml',
        'wizard/multi_add_shipping_wizard_views.xml',
        'views/delivery_grab_views.xml',
        'views/stock_picking_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/grab_status_views.xml',
        'views/grab_promo_code_views.xml',
        'views/grab_routes_api_views.xml',
        'views/grab_delivery_order_views.xml',
        'views/sale_order_views.xml',
        'views/menus.xml'
    ],
    'images': ['static/description/thumbnail.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'currency': 'USD',
    'price': 98.00
}