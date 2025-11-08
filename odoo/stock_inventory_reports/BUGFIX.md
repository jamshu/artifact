# Bug Fix - Return Report Error Handling

## Issue Encountered

**Error Message:**
```
File ".../return_report_wizard.py", line 174, in _generate_excel_report
    worksheet.write(row, 7, line['return_reason'], cell_format)
KeyError: 'return_reason'
```

## Root Cause

The error occurred because the `return_reason` field was being accessed on `sale.order.line` model without checking if the field exists. If the custom field `return_reason` doesn't exist on the `sale.order.line` model, the code would crash.

## Solution Applied

### Code Change

**File:** `wizards/return_report_wizard.py`  
**Line:** 105

**Before:**
```python
if sale_line:
    return_reason = sale_line.return_reason or ''
```

**After:**
```python
if sale_line:
    # Safely get return_reason field if it exists
    return_reason = getattr(sale_line, 'return_reason', '') or ''
```

### How It Works

The `getattr()` function safely retrieves the field value:
- **If field exists:** Returns the field value
- **If field doesn't exist:** Returns the default value (empty string `''`)
- **The `or ''` ensures:** Even if the field value is `False` or `None`, we get an empty string

## Benefits

✅ **Graceful Degradation:** Report works even without custom field  
✅ **No Crashes:** Safe field access prevents KeyError  
✅ **Flexibility:** Users can add the field later  
✅ **Better UX:** Empty column instead of error message  

## Custom Field Requirement

For the Return Reason column to show data, add this field to your Odoo instance:

```python
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    return_reason = fields.Char(string='Return Reason')
```

## Testing

To verify the fix:

### Test 1: Without Custom Field
1. Generate return report
2. ✅ Report should generate successfully
3. ✅ Return Reason column should be empty

### Test 2: With Custom Field
1. Add `return_reason` field to `sale.order.line`
2. Add return reasons to some sale order lines
3. Generate return report
4. ✅ Report should show return reasons

## Additional Improvements

The same safe access pattern should be applied to other custom fields:

### File: `return_report_wizard.py`

**Line 76:** `sale_line.order_id.employee_id`
- Already safe (uses `and` chaining)
- ✅ No change needed

**Line 88:** `move.picking_id.sale_id`
- Already safe (uses `and` chaining)
- ✅ No change needed

## Documentation Updated

The following files were updated to document this:

1. **INSTALL.md** - Added troubleshooting section
2. **BUGFIX.md** - This file
3. **README.md** - Already mentions custom field requirement

## Prevention

To prevent similar issues in the future:

1. ✅ Use `getattr()` for custom fields
2. ✅ Provide default values
3. ✅ Document custom field requirements
4. ✅ Test with and without custom fields

## Status

✅ **FIXED** - Module now handles missing custom fields gracefully
