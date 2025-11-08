# Stock Inventory Reports

## Overview
This module provides advanced inventory reporting features for Odoo 16.0, including:
- **Scrap Report**: Detailed reporting on scrapped inventory items
- **Return Report**: Comprehensive customer return tracking and reporting
- **Centralized Dashboard**: Single entry point to access all inventory reports

## Features

### Main Dashboard
- Single wizard with buttons to access different reports
- Reduces menu clutter by consolidating report access

### Scrap Report
Generates Excel reports for scrapped inventory with the following columns:
- Date
- Product Name
- Product Reference
- Operation Type
- Quantity
- Unit of Measure
- Reason (Source document field of stock picking)
- Remarks (Note field of stock picking)

**Filters:**
- Date Range (Mandatory)
- Warehouse (Many2many - Mandatory)
- Location (Many2many - Optional)
- Operation Type (Many2many - Optional)
- Product Category (Many2many - Optional)
- Product (Many2many - Optional)

**Logic:**
- Automatically identifies operation types with scrap locations as destination
- Filters stock moves based on provided criteria
- Exports data to Excel format

### Return Report
Generates Excel reports for customer returns with the following columns:
- Date
- Return Invoice Number (Blank if no invoice created)
- Customer Name
- Product Name
- Product Reference
- Quantity
- Salesperson
- Return Reason (From sales order line)
- Received By (User who validated the picking)

**Filters:**
- Date Range (Mandatory)
- Warehouse (Many2many - Mandatory)
- Location (Many2many - Optional)
- Operation Type (Many2many - Optional)
- Product Category (Many2many - Optional)
- Product (Many2many - Optional)
- Salesman (Many2many - Optional, hr.employee)

**Logic:**
- Finds customer return stock moves using custom field `picking_kind == "customer_return"`
- Links to sales order lines and invoices via sale.order.employee_id field
- Filters based on provided criteria
- Exports data to Excel format

## Technical Details

### Abstract Models
The module uses several abstract models for code reusability:
- `base.date.range.wizard`: Date range selection with validation
- `base.excel.report.wizard`: Common Excel generation and download logic
- `base.warehouse.wizard`: Warehouse selection
- `base.location.wizard`: Location selection
- `base.operation.type.wizard`: Operation type selection
- Inherits from `base.product.categ.wizard`: Product category and product selection

### Dependencies
- `stock`: Core inventory module
- `sale_stock`: Sales and stock integration
- `account`: Accounting for invoice tracking
- `product_base`: Product category wizard
- `hr`: Human Resources (for employee/salesperson data)
- **Python**: `xlsxwriter` library for Excel generation

### Installation
1. Ensure `xlsxwriter` Python library is installed:
   ```bash
   pip install xlsxwriter
   ```
2. Copy the module to your addons directory
3. Update the apps list in Odoo
4. Install the module

### Usage
1. Navigate to **Inventory > Inventory Reports > Reports Dashboard**
2. Click on the desired report button (Scrap Report or Return Report)
3. Fill in the filter criteria
4. Click "Generate Report" to download the Excel file

Alternatively, you can access reports directly from:
- **Inventory > Inventory Reports > Scrap Report**
- **Inventory > Inventory Reports > Return Report**

## Module Structure
```
stock_inventory_reports/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── abstract_report_wizard.py
├── wizards/
│   ├── __init__.py
│   ├── inventory_report_dashboard.py
│   ├── scrap_report_wizard.py
│   └── return_report_wizard.py
├── views/
│   └── menu_views.xml
├── wizards/
│   ├── inventory_report_dashboard_views.xml
│   ├── scrap_report_wizard_views.xml
│   └── return_report_wizard_views.xml
└── security/
    └── ir.model.access.csv
```

## Configuration
No additional configuration required after installation.

## Known Issues / Limitations
- Requires custom field `picking_kind` on `stock.picking` model for return report functionality
- Requires custom field `employee_id` on `sale.order` model for salesperson tracking (hr.employee)
- Excel generation requires `xlsxwriter` Python library

## Support
For issues or questions, please contact your system administrator.

## License
LGPL-3

## Author
Your Company

## Version
16.0.1.0.0
