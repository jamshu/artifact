{
    'name': 'Invoice Generated for Stock ',
    'version': '0.1.12',
    'category': 'Inventory/Inventory',
    'author' : 'Shoaib Anwar',
    'website': 'shoaib.anwar0707@gmail.com',
    'depends': ['purchase_stock','stock_picking_invoice_link'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/purchase_order.xml',
        'views/account_move_view.xml',
        'wizards/picking_invoice_wizard.xml',
    ],
}
