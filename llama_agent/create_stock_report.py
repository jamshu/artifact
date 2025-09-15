#!/usr/bin/env python3
"""
Script to create the Product Stock Report module using Gemini agent
"""

from gemini_odoo_agent import GeminiOdooAgent
import json

def create_product_stock_report():
    """Create the product stock report module"""
    
    # Configure for Odoo 15.0 (based on your .env)
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    # Use the path from your .env
    addons_path = os.getenv('ODOO_ADDONS_PATH', '/Users/jamshid/PycharmProjects/Siafa15/odoo15e_siafa/addons-product/')
    odoo_version = os.getenv('ODOO_VERSION', '15.0')
    
    print(f"🔧 Creating module in: {addons_path}")
    print(f"📦 Target Odoo version: {odoo_version}")
    
    # Initialize agent
    agent = GeminiOdooAgent()
    # Update paths to use your configuration
    from pathlib import Path
    agent.odoo_addons_path = Path(addons_path)
    agent.odoo_version = odoo_version
    
    # Module details
    module_name = "product_stock_report"
    description = "Product Stock Report - Extract data from product.stock.v16 table with advanced wizard"
    features = """
    Advanced reporting wizard with:
    - Fancy, user-friendly wizard interface
    - Date range selection with calendar widgets  
    - Company selection (default to current user's company)
    - Location selection with multi-select capability
    - Report generation from existing product.stock.v16 table
    
    Report structure:
    - Header: Display selected Date, User, and Location
    - Table columns: Product Name, Product Reference, UoM, Stock Quantity
    - Export options: PDF and Excel
    - Print functionality
    - Advanced filtering and sorting
    - Responsive design for mobile/desktop
    
    Technical features:
    - Uses existing product.stock.v16 database view/table
    - Optimized SQL queries for performance
    - Multi-company support
    - Access rights and security groups
    - Odoo 15.0 compatible patterns
    """
    
    print("\n🤖 Generating Product Stock Report module...")
    print("=" * 60)
    
    try:
        # Create the module
        result = agent.create_odoo_module(module_name, description, features)
        
        if result['success']:
            print(f"\n✅ Module created successfully!")
            print(f"📁 Module path: {result['module_path']}")
            print(f"📄 Files created: {result['files_created']}")
            
            print(f"\n📋 Next steps:")
            print(f"1. Copy the module to your Odoo addons directory")
            print(f"2. Update your Odoo app list")
            print(f"3. Install the 'Product Stock Report' module")
            print(f"4. Navigate to Inventory > Reports > Product Stock Report")
            
            return result
        else:
            print(f"\n❌ Error creating module: {result.get('error', result.get('message', 'Unknown error'))}")
            return result
            
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    create_product_stock_report()