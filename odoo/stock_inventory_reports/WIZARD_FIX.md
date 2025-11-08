# Fix: Wizard Freeze After Report Generation

## Issue

After generating a report (Scrap or Return), the wizard would freeze and users couldn't change filters or generate another report without closing and reopening the wizard.

## Root Cause

The original implementation returned an `ir.actions.act_url` action that would close the wizard after downloading the file, making it impossible to generate multiple reports without reopening the wizard.

## Solution

Changed the return action to use `ir.actions.client` with `display_notification` tag, which:
1. Shows a success notification to the user
2. Automatically triggers the Excel download
3. **Keeps the wizard open** for generating additional reports

## Code Changes

### File: `models/abstract_report_wizard.py`

**Method:** `action_generate_report()` in `BaseExcelReportWizard` class

**Before:**
```python
return {
    'type': 'ir.actions.act_url',
    'url': f'/web/content?model={self._name}&id={self.id}&field=excel_file&filename_field=excel_filename&download=true',
    'target': 'self',
}
```

**After:**
```python
# Show success message and trigger download
message = _('Report generated successfully! Download will start automatically.')

return {
    'type': 'ir.actions.client',
    'tag': 'display_notification',
    'params': {
        'title': _('Success'),
        'message': message,
        'type': 'success',
        'sticky': False,
        'next': {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model={self._name}&id={self.id}&field=excel_file&filename_field=excel_filename&download=true',
            'target': 'self',
        },
    },
}
```

## Benefits

✅ **Wizard stays open** - Users can generate multiple reports  
✅ **Better UX** - Success notification confirms generation  
✅ **Automatic download** - File downloads immediately  
✅ **Easy filter changes** - Modify filters and regenerate  
✅ **Time saving** - No need to reopen wizard each time  

## User Experience

### Before Fix
1. User opens wizard
2. Sets filters
3. Clicks "Generate Report"
4. Excel downloads
5. ❌ Wizard closes/freezes
6. Must reopen wizard to generate another report

### After Fix
1. User opens wizard
2. Sets filters
3. Clicks "Generate Report"
4. ✅ Success notification appears
5. ✅ Excel downloads automatically
6. ✅ Wizard stays open and active
7. ✅ User can change filters
8. ✅ Click "Generate Report" again
9. ✅ Process repeats seamlessly

## Testing

To verify the fix works:

### Test 1: Generate Single Report
1. Open Scrap Report or Return Report wizard
2. Fill in filters (dates, warehouse, etc.)
3. Click "Generate Report"
4. ✅ Success notification should appear
5. ✅ Excel file should download
6. ✅ Wizard should remain open

### Test 2: Generate Multiple Reports
1. Follow Test 1 steps
2. Change some filters (e.g., different date range)
3. Click "Generate Report" again
4. ✅ Second report should generate
5. ✅ Second Excel file should download
6. ✅ Wizard should still be open

### Test 3: Different Filter Combinations
1. Generate report with all warehouses
2. ✅ Report generates successfully
3. Change to specific warehouse only
4. ✅ Generate again successfully
5. Add product category filter
6. ✅ Generate again successfully
7. ✅ All actions complete without freezing

## Technical Details

### Notification Action
The `ir.actions.client` action with `display_notification` tag is a standard Odoo pattern for showing notifications.

**Parameters:**
- `title`: Notification title (e.g., "Success")
- `message`: Notification message
- `type`: Notification type (`success`, `warning`, `danger`, `info`)
- `sticky`: Whether notification stays on screen (False = auto-dismiss)
- `next`: Next action to execute after showing notification

### Download Trigger
The `next` parameter contains an `ir.actions.act_url` action that:
- Points to the web content download URL
- Uses `target: 'self'` to download in same window
- Triggers browser's download functionality
- Does NOT close the wizard

## Applies To

This fix applies to:
- ✅ Scrap Report Wizard
- ✅ Return Report Wizard
- ✅ Any future reports using `BaseExcelReportWizard`

## Status

✅ **FIXED** - Wizards now stay open after report generation
