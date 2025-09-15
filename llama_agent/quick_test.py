#!/usr/bin/env python3

from odoo_agent import OdooAIAgent, OdooAgentConfig

def quick_test():
    """Quick test with manual module creation"""
    
    config = OdooAgentConfig(
        ollama_model="llama3.2",  # Faster model
        repository_path="./test_modules",
        chroma_db_path="./chroma_db"
    )
    
    agent = OdooAIAgent(config)
    
    print("🧪 Creating sample Odoo module structure...")
    
    # Manually create a sample module structure to demonstrate
    from pathlib import Path
    
    module_path = Path("./test_modules/sample_inventory")
    module_path.mkdir(exist_ok=True)
    
    # Create subdirectories
    for subdir in ['models', 'views', 'security', 'data', 'static/description']:
        (module_path / subdir).mkdir(parents=True, exist_ok=True)
    
    # Create sample files
    
    # __manifest__.py
    manifest_content = """{
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
}"""
    
    # __init__.py
    init_content = "from . import models"
    
    # models/__init__.py
    models_init_content = "from . import product_template"
    
    # models/product_template.py
    product_model_content = """from odoo import models, fields, api

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
"""
    
    # Write files
    (module_path / '__manifest__.py').write_text(manifest_content)
    (module_path / '__init__.py').write_text(init_content)
    (module_path / 'models' / '__init__.py').write_text(models_init_content)
    (module_path / 'models' / 'product_template.py').write_text(product_model_content)
    
    print(f"✅ Sample module created at: {module_path}")
    print(f"📁 Files created:")
    print(f"  - __manifest__.py")
    print(f"  - __init__.py")
    print(f"  - models/__init__.py")
    print(f"  - models/product_template.py")
    
    print(f"\n📄 Sample model code:")
    print("=" * 60)
    print(product_model_content[:500] + "...")
    print("=" * 60)
    
    return {"success": True, "module_path": str(module_path)}

if __name__ == "__main__":
    quick_test()