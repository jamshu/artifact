# Quick Reference - Stock Inventory Reports

## Module Information
- **Name**: Stock Inventory Reports
- **Technical Name**: `stock_inventory_reports`
- **Version**: 16.0.1.0.0
- **Location**: `addons-stock/stock_inventory_reports/`

## Quick Start

### Installation
```bash
# 1. Install Python dependency
pip install xlsxwriter

# 2. In Odoo:
# - Apps > Update Apps List
# - Search "Stock Inventory Reports"
# - Click Install
```

### Access Reports
Navigate to: **Inventory > Inventory Reports**
- **Reports Dashboard** (main entry point)
- **Scrap Report** (direct access)
- **Return Report** (direct access)

## Reports Overview

### 1. Scrap Report
**Purpose**: Track scrapped inventory items

**Mandatory Filters:**
- Date From
- Date To
- Warehouse(s)

**Optional Filters:**
- Location(s)
- Operation Type(s)
- Product Category(ies)
- Product(s)

**Output Columns:**
Date | Product Name | Product Reference | Operation Type | Quantity | UoM | Reason | Remarks

### 2. Return Report
**Purpose**: Track customer returns with sales information

**Mandatory Filters:**
- Date From
- Date To
- Warehouse(s)

**Optional Filters:**
- Location(s)
- Operation Type(s)
- Product Category(ies)
- Product(s)
- Salesperson(s) - hr.employee

**Output Columns:**
Date | Invoice # | Customer | Product Name | Product Ref | Quantity | Salesperson | Return Reason | Received By

## Custom Fields Required

### stock.picking
```python
picking_kind = fields.Selection([
    ('customer_return', 'Customer Return'),
], string='Picking Kind')
```

### sale.order
```python
employee_id = fields.Many2one('hr.employee', string='Salesperson')
```

### sale.order.line
```python
return_reason = fields.Char(string='Return Reason')
```

## Common Operations

### Generate Scrap Report
1. Go to **Inventory > Inventory Reports > Scrap Report**
2. Select date range
3. Select warehouse(s)
4. Optionally add other filters
5. Click **Generate Report**
6. Excel file downloads automatically

### Generate Return Report
1. Go to **Inventory > Inventory Reports > Return Report**
2. Select date range
3. Select warehouse(s)
4. Optionally select salesperson(s) and other filters
5. Click **Generate Report**
6. Excel file downloads automatically

### Use Dashboard
1. Go to **Inventory > Inventory Reports > Reports Dashboard**
2. Click **Scrap Report** or **Return Report** button
3. Fill in filters in popup wizard
4. Click **Generate Report**
5. Excel file downloads automatically

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "xlsxwriter not found" | `pip install xlsxwriter` then restart Odoo |
| "No data found" | Check date range and filters, ensure data exists |
| "Access Rights" error | User needs Stock User or Stock Manager group |
| No salesperson shown | Check sale.order has employee_id filled |
| Report not in menu | Update Apps List and check module is installed |

## File Naming Convention
- Scrap Report: `Scrap_Report_YYYY-MM-DD_YYYY-MM-DD.xlsx`
- Return Report: `Return_Report_YYYY-MM-DD_YYYY-MM-DD.xlsx`

## User Permissions
- **Stock User**: Can generate all reports
- **Stock Manager**: Can generate all reports

## Technical Support
For issues or customizations, contact your system administrator.

## Module Files
```
stock_inventory_reports/
├── models/               # Abstract wizard models
├── wizards/              # Report wizards and views
├── views/                # Menu definitions
├── security/             # Access rights
├── README.md             # Full documentation
├── INSTALL.md            # Installation guide
├── CHANGELOG.md          # Version history
└── QUICK_REFERENCE.md    # This file
```
