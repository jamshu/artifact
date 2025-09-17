# -*- coding: utf-8 -*-
{
    'name': 'POS Geidea Integration',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Jamshid K',
    'website': 'www.siafadate.com',
    'summary': 'Integrate Geidea Payment Terminal with Odoo POS',
    'description': """
        Integrate Geidea payment terminals with Odoo Point of Sale:
        - Support for card payments via Geidea terminal
        - Store transaction details
        - Print payment receipts
    """,
    'depends': ['point_of_sale', 'pos_sync_v16'],
    'data': [
        'views/pos_payment_method_views.xml',
        
    ],
    'assets': {
        'point_of_sale.assets': [
             'pos_geidea/static/src/js/models.js',
            'pos_geidea/static/src/js/logging_client.js',
            'pos_geidea/static/src/js/payment.js',
            'pos_geidea/static/src/js/payment_screen.js',
            'pos_geidea/static/src/js/payment_status_fix.js',
            'pos_geidea/static/src/js/clear_payment_on_back.js',
            'pos_geidea/static/src/js/payment_restrictions.js',
            'pos_geidea/static/src/css/pos_geidea.scss',

        ],
        'web.assets_qweb': [
         
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}