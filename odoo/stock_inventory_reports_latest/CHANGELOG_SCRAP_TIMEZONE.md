# Scrap Report & Return Report Updates

## Date: 2025-10-11

## Summary of Changes

This document outlines the recent enhancements made to both the Scrap Report and Return Report modules.

---

## 1. Scrap Report Enhancement: Bidirectional Movement Tracking

### Problem
The scrap report was only showing items that were scrapped (moved TO scrap locations), but not items that were returned FROM scrap locations back to inventory. This gave an incomplete picture of scrap movements.

### Solution
Updated the scrap report to track both directions of movement:

#### Changes in `wizards/scrap_report_wizard.py`:

1. **Modified `_get_report_data()` method**:
   - Now performs TWO separate searches for stock moves:
     - **TO scrap locations** (`location_dest_id` = scrap location): Shows as **positive quantity**
     - **FROM scrap locations** (`location_id` = scrap location): Shows as **negative quantity**
   
2. **Added new fields to report data**:
   - `scrap_location`: The scrap location involved in the movement
   - `other_location`: The non-scrap location (source or destination)
   
3. **Improved filtering logic**:
   - When filtering by warehouse, correctly handles both directions:
     - For scrapping: source location must be in warehouse
     - For returns: destination location must be in warehouse

#### Changes in `reports/scrap_report_xlsx.py`:

1. **Added two new columns**:
   - **Scrap Location**: Shows which scrap location was involved
   - **Other Location**: Shows the source/destination location (non-scrap)

2. **Updated column widths** to accommodate the new columns

### Benefits
- **Complete picture**: See both scrap-out and return-from-scrap movements
- **Accurate totals**: When an item is mistakenly scrapped and then returned, you'll see both movements and the net total will be zero
- **Better tracking**: Easily identify which scrap location was involved in each movement

---

## 2. Timezone Conversion for Both Reports

### Problem
Dates in both Scrap Report and Return Report Excel files were showing in UTC time, not matching what users see in the Odoo UI (which shows dates in the user's timezone).

### Solution
Implemented proper timezone conversion in both report generators.

#### Changes in `reports/scrap_report_xlsx.py`:

1. **Added imports**:
   ```python
   from odoo import models, fields
   from datetime import datetime
   import pytz
   ```

2. **Get user timezone**:
   ```python
   user_tz = self.env.user.tz or 'UTC'
   tz = pytz.timezone(user_tz)
   ```

3. **Convert dates before writing to Excel**:
   - Parse datetime from string if needed
   - Localize to UTC if timezone-naive
   - Convert to user's timezone
   - Remove timezone info for Excel (Excel stores naive datetimes)

#### Changes in `reports/return_report_xlsx.py`:

Applied the same timezone conversion logic as in the scrap report.

### Benefits
- **Consistent with Odoo UI**: Dates in Excel now match exactly what users see in Odoo
- **User-friendly**: Each user sees dates in their own timezone
- **No confusion**: Eliminates discrepancies between UI and Excel reports

---

## Example: Scrap Report with Bidirectional Tracking

**Scenario**: An item was mistakenly scrapped on 2025-10-10, then returned from scrap on 2025-10-11.

### Old Report (Before Changes):
```
Date       | Product | Qty | Scrap Location
2025-10-10 | Widget  | 5.0 | VWH/Scrap
```
**Net result**: Looks like 5 items are still scrapped (incomplete)

### New Report (After Changes):
```
Date       | Product | Qty  | Scrap Location | Other Location | 
2025-10-10 | Widget  |  5.0 | VWH/Scrap      | VWH/Stock      |
2025-10-11 | Widget  | -5.0 | VWH/Scrap      | VWH/Stock      |
```
**Net result**: 0 items in scrap (accurate and complete)

---

## Deployment Instructions

1. **Upgrade the module**:
   ```bash
   odoo-bin -u stock_inventory_reports -d your_database
   ```

2. **Restart Odoo** (recommended):
   ```bash
   sudo systemctl restart odoo
   ```

3. **Test the reports**:
   - Open Inventory Dashboard
   - Click "Scrap Report" button
   - Set date range and filters
   - Generate report
   - Verify:
     - Dates match Odoo UI (in your timezone)
     - Both scrap-out and return-from-scrap movements appear
     - Return movements show negative quantities
     - New columns (Scrap Location, Other Location) are present

4. **Test Return Report timezone**:
   - Click "Return Report" button
   - Generate report
   - Verify dates match Odoo UI

---

## Technical Notes

### Timezone Conversion Process:
```python
# 1. Get date from database (UTC)
date_utc = line['date']

# 2. Convert string to datetime if needed
if isinstance(date_utc, str):
    date_utc = fields.Datetime.from_string(date_utc)

# 3. Ensure timezone is set to UTC
date_utc = pytz.UTC.localize(date_utc) if date_utc.tzinfo is None else date_utc

# 4. Convert to user's timezone
date_local = date_utc.astimezone(tz)

# 5. Remove timezone for Excel (Excel stores naive datetimes)
date_naive = date_local.replace(tzinfo=None)

# 6. Write to Excel
worksheet.write_datetime(current_row, 0, date_naive, date_format)
```

### Scrap Report Bidirectional Logic:
```python
# Search 1: TO scrap (positive quantity)
to_scrap_domain = [
    ('location_dest_id', 'in', scrap_location_ids),
    ('location_id', 'in', warehouse_location_ids),  # Source in warehouse
    ...
]

# Search 2: FROM scrap (negative quantity)
from_scrap_domain = [
    ('location_id', 'in', scrap_location_ids),
    ('location_dest_id', 'in', warehouse_location_ids),  # Dest in warehouse
    ...
]
```

---

## Files Modified

1. `wizards/scrap_report_wizard.py` - Enhanced data retrieval logic
2. `reports/scrap_report_xlsx.py` - Added columns and timezone conversion
3. `reports/return_report_xlsx.py` - Added timezone conversion

---

## Future Enhancements (Optional)

Consider these additions:
1. Add a "Net Quantity" summary per product in scrap report
2. Add color coding: green for returns (negative), red for scraps (positive)
3. Add pivot table or summary sheet with totals by scrap location
4. Add filtering by movement direction (in/out/both)

---

## Questions or Issues?

If you encounter any issues:
1. Verify `pytz` is installed: `pip3 install pytz`
2. Check user timezone is set: Settings → Users → User → Preferences → Timezone
3. Verify scrap locations have `scrap_location = True` flag
4. Check Odoo logs for any errors
