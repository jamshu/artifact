from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Custom fields for enhanced inventory tracking
    inventory_priority = fields.Selection([
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical')
    ], string='Inventory Priority', default='medium')
    
    min_stock_level = fields.Float(
        string='Minimum Stock Level',
        help='Alert when stock goes below this level'
    )
    
    max_stock_level = fields.Float(
        string='Maximum Stock Level',
        help='Maximum recommended stock level'
    )
    
    last_inventory_date = fields.Datetime(
        string='Last Inventory Check',
        help='Date of last physical inventory check'
    )
    
    @api.depends('qty_available', 'min_stock_level')
    def _compute_stock_status(self):
        for product in self:
            if product.qty_available < product.min_stock_level:
                product.stock_status = 'low'
            elif product.qty_available > product.max_stock_level:
                product.stock_status = 'high'
            else:
                product.stock_status = 'normal'
    
    stock_status = fields.Selection([
        ('low', 'Low Stock'),
        ('normal', 'Normal Stock'),
        ('high', 'Overstock')
    ], string='Stock Status', compute='_compute_stock_status', store=True)
