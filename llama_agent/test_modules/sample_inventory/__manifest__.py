{
    'name': 'Sample Inventory Management',
    'version': '16.0.1.0.0',
    'summary': 'Enhanced inventory management features',
    'description': '''
        This module provides enhanced inventory management features including:
        - Custom product attributes
        - Advanced stock tracking
        - Inventory reporting
    ''',
    'author': 'AI Generated',
    'website': 'https://www.example.com',
    'category': 'Inventory',
    'depends': ['stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'data/product_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}