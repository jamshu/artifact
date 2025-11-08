# -*- coding: utf-8 -*-
{
    'name': 'Stock Inventory Reports',
    'version': '16.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Advanced inventory reports including Scrap and Return reports',
    'description': """
        Stock Inventory Reports
       
        This module provides advanced inventory reporting features:
        - Scrap Report with detailed filtering
        - Return Report with invoice and sales information
        - Centralized dashboard to access all reports
    """,
    'author': 'Your Company',
    'depends': ['stock', 'sale_stock', 'account', 'product_base', 'hr', 'sale_order_return_reason', 'report_xlsx'],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/report_actions.xml',
        'wizards/inventory_report_dashboard_views.xml',
        'wizards/scrap_report_wizard_views.xml',
        'wizards/return_report_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
