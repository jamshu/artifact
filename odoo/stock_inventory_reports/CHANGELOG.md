# Changelog - Stock Inventory Reports

## Version 16.0.1.0.0

### Initial Release

#### Features Implemented

**1. Main Dashboard**
- Single entry point wizard with buttons to access all reports
- Reduces menu clutter by consolidating report access
- Opens child wizards in popup windows

**2. Scrap Report**
- Excel report generation for scrapped inventory items
- Automatic identification of scrap locations
- Comprehensive filtering options:
  - Date Range (Mandatory)
  - Warehouse (M2M - Mandatory)
  - Location (M2M - Optional)
  - Operation Type (M2M - Optional)
  - Product Category (M2M - Optional)
  - Product (M2M - Optional)

**Report Columns:**
- Date
- Product Name
- Product Reference
- Operation Type
- Quantity
- Unit of Measure
- Reason (from stock.picking.origin)
- Remarks (from stock.picking.note)

**3. Return Report**
- Excel report generation for customer returns
- Links to sales orders, invoices, and employee data
- Comprehensive filtering options:
  - Date Range (Mandatory)
  - Warehouse (M2M - Mandatory)
  - Location (M2M - Optional)
  - Operation Type (M2M - Optional)
  - Product Category (M2M - Optional)
  - Product (M2M - Optional)
  - Salesperson (M2M - Optional, hr.employee)

**Report Columns:**
- Date
- Return Invoice Number (blank if no invoice)
- Customer Name
- Product Name
- Product Reference
- Quantity
- Salesperson (from sale.order.employee_id - hr.employee)
- Return Reason (from sale.order.line.return_reason)
- Received By (user who validated the picking)

#### Technical Architecture

**Abstract Models Created:**
- `base.date.range.wizard`: Date range selection with validation
- `base.excel.report.wizard`: Common Excel generation and download logic
- `base.warehouse.wizard`: Warehouse selection
- `base.location.wizard`: Location selection
- `base.operation.type.wizard`: Operation type selection
- Inherits from `base.product.categ.wizard`: Product category and product selection

**Code Reusability:**
- Common Excel generation logic abstracted to parent class
- Report filename generation handled automatically
- Consistent filtering patterns across all reports

**Dependencies:**
- `stock`: Core inventory module
- `sale_stock`: Sales and stock integration
- `account`: Accounting for invoice tracking
- `product_base`: Product category wizard (custom module)
- `hr`: Human Resources for employee/salesperson data
- **Python**: `xlsxwriter` library for Excel generation

#### Custom Field Requirements

The module expects the following custom fields to exist in your Odoo instance:

**1. On `stock.picking` model:**
```python
picking_kind = fields.Selection([
    ('customer_return', 'Customer Return'),
    # ... other values
], string='Picking Kind')
```

**2. On `sale.order` model:**
```python
employee_id = fields.Many2one(
    'hr.employee',
    string='Salesperson'
)
```

**3. On `sale.order.line` model:**
```python
return_reason = fields.Char(string='Return Reason')
```

#### Menu Structure
- **Inventory > Inventory Reports**
  - Reports Dashboard (main entry point)
  - Scrap Report (direct access)
  - Return Report (direct access)

#### Security
- Access rights configured for:
  - Stock User group
  - Stock Manager group
- All transient models properly secured

#### Excel Export Features
- Professional formatting with headers
- Bordered cells for clarity
- Date/time formatting
- Number formatting with decimals
- Text wrapping for long content
- Auto-sized columns for optimal viewing

### Notes
- All reports export to Excel format (.xlsx)
- Transient models (wizards) don't persist data in database
- Reports filter only completed stock moves (state='done')
- Salesperson filtering uses hr.employee, not res.users

### Known Limitations
- Requires custom fields as listed above
- Excel generation requires xlsxwriter Python library
- Return report requires `picking_kind` field for identification
- Salesperson tracking requires `employee_id` on sale.order

### Future Enhancements (Potential)
- Additional report types (e.g., Stock Movement, Valuation)
- PDF export option
- Scheduled report generation
- Email delivery of reports
- Custom report templates
- Additional filtering options
