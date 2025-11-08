# Installation Guide - Stock Inventory Reports

## Prerequisites

### Python Dependencies
This module requires the `xlsxwriter` library. Install it using pip:

```bash
pip install xlsxwriter
```

### Odoo Dependencies
The following Odoo modules must be installed:
- `stock` (Core Inventory)
- `sale_stock` (Sales and Stock Integration)
- `account` (Accounting)
- `product_base` (Custom module for product category wizard)
- `hr` (Human Resources for employee/salesperson data)

## Installation Steps

### 1. Module Placement
The module is already placed in the correct location:
```
addons-stock/stock_inventory_reports/
```

### 2. Update Apps List
In Odoo, go to:
- **Apps** menu
- Click on the three-dot menu (⋮)
- Select **Update Apps List**

### 3. Install the Module
- Search for "Stock Inventory Reports"
- Click **Install**

## Post-Installation Verification

### 1. Check Menu Items
Navigate to **Inventory > Inventory Reports** and verify:
- Reports Dashboard
- Scrap Report
- Return Report

### 2. Test Dashboard
1. Go to **Inventory > Inventory Reports > Reports Dashboard**
2. Verify buttons appear:
   - Scrap Report button
   - Return Report button
3. Click each button to ensure wizards open correctly

### 3. Test Scrap Report
1. Open **Inventory > Inventory Reports > Scrap Report**
2. Fill in mandatory fields:
   - Date From
   - Date To
   - Warehouse(s)
3. Click **Generate Report**
4. Verify Excel file downloads

### 4. Test Return Report
1. Open **Inventory > Inventory Reports > Return Report**
2. Fill in mandatory fields:
   - Date From
   - Date To
   - Warehouse(s)
3. Click **Generate Report**
4. Verify Excel file downloads

## Troubleshooting

### Issue: "xlsxwriter not found" error
**Solution:** Install xlsxwriter:
```bash
pip install xlsxwriter
```
Then restart Odoo server.

### Issue: "Module not found" error
**Solution:** 
1. Check that the module is in the addons path
2. Update the apps list
3. Restart Odoo server if necessary

### Issue: "Access Rights" error
**Solution:**
- Ensure user has one of these groups:
  - Inventory / User
  - Inventory / Administrator

### Issue: "No data found" message
**Solution:**
- Check that you have stock moves in the selected date range
- For Scrap Report: Ensure scrap locations exist and have movements
- For Return Report: Ensure pickings with `picking_kind='customer_return'` exist

### Issue: Return Report shows no salesperson
**Solution:**
- Verify that stock moves are linked to sales orders
- Check that sales orders have an employee assigned in the `employee_id` field (hr.employee)
- Ensure the `employee_id` field exists on the `sale.order` model

### Issue: "Field 'return_reason' does not exist" error
**Solution:**
- The `return_reason` field needs to exist on `sale.order.line` model
- If the field doesn't exist, the report will show blank for return reason
- To add the field, create a custom module with:
  ```python
  class SaleOrderLine(models.Model):
      _inherit = 'sale.order.line'
      
      return_reason = fields.Char(string='Return Reason')
  ```
- Alternatively, you can modify line 105 in `return_report_wizard.py` to use a different field

## Custom Field Requirements

### For Return Report
The Return Report requires the following custom fields:

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

If these fields don't exist in your system, you'll need to:
1. Create them in a custom module, or
2. Modify the return report logic to use alternative identification methods

## Uninstallation

To uninstall the module:
1. Go to **Apps**
2. Search for "Stock Inventory Reports"
3. Click **Uninstall**

**Note:** All wizard data will be removed (transient models).

## Support

For technical support or customization requests, contact your system administrator or module developer.
