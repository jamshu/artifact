# -*- coding: utf-8 -*-
{
    'name': "Inventory Adjustment Barcode",
    'summary': "Inventory Adjustment Using Barcode",
    'description': """
    - This Module is used for adjust mismatch stock using barcode scanner
    """,

    'website': 'https://www.ksolves.com',
    'category': 'Inventory',
    'version': '16.0.1.0.0',

    'depends': ['stock_account', 'barcodes', 'base_product_cost_security', 'mrp_bom_transfer_auto'],

    'data': [
        'security/ir.model.access.csv',
        'security/stock_adjustment_barcode_group.xml',
        'data/stock_adjustment_barcode_data.xml',
        'report/inv_cost_analysis_report_action.xml',
        'report/inv_cost_analysis_report_views.xml',
        'report/stock_variation_report.xml',
        'views/stock_adjustment_barcode_line_info_views.xml',
        'views/stock_adjustment_barcode_lot_line.xml',
        'views/stock_adjustment_barcode_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'stock_adjustment_barcode/static/src/css/stock_adjustment_barcode.css',
        ],
        'web.report_assets_common': [
            'stock_adjustment_barcode/static/src/scss/inv_cost_analysis_report.scss',
        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
