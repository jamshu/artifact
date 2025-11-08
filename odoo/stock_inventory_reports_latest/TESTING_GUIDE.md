# Testing Guide: Scrap Report & Timezone Conversion

## Quick Test Checklist

### ✅ Test 1: Timezone Conversion

**Objective**: Verify dates in Excel match Odoo UI

**Steps**:
1. Set your user timezone (Settings → Users → Your User → Preferences → Timezone)
2. Create a test scrap picking with a specific date/time (note the exact time in Odoo UI)
3. Generate Scrap Report
4. Open Excel file
5. **Verify**: Date/time in Excel matches exactly what you saw in Odoo UI

**Example**:
- Odoo UI shows: `2025-10-11 14:30:00` (Dubai time, GMT+4)
- Excel should show: `2025-10-11 14:30:00` (NOT `2025-10-11 10:30:00` UTC)

---

### ✅ Test 2: Bidirectional Scrap Tracking

**Objective**: Verify both scrap-out and return-from-scrap movements appear

**Setup**:
1. Create a scrap location (if not exists): `VWH/Scrap` with `scrap_location = True`
2. Create a test product: `Test Widget`

**Test Scenario**:

**Step 1 - Scrap an item**:
1. Create internal transfer or scrap order
2. Move 10 units of `Test Widget` FROM `VWH/Stock` TO `VWH/Scrap`
3. Validate the transfer
4. Note the date/time

**Step 2 - Return from scrap**:
1. Create internal transfer
2. Move 5 units of `Test Widget` FROM `VWH/Scrap` TO `VWH/Stock`
3. Validate the transfer
4. Note the date/time

**Step 3 - Generate Report**:
1. Open Inventory Dashboard
2. Click "Scrap Report"
3. Select date range covering both movements
4. Generate report

**Expected Results**:
```
Date       | Product      | Qty  | Scrap Location | Other Location
----------|--------------|------|----------------|----------------
2025-10-11| Test Widget  | 10.0 | VWH/Scrap      | VWH/Stock
2025-10-11| Test Widget  | -5.0 | VWH/Scrap      | VWH/Stock
```

**Verify**:
- ✅ Both movements appear in report
- ✅ First movement (scrap) shows +10.0
- ✅ Second movement (return) shows -5.0
- ✅ Net effect: 5 units still in scrap (10 - 5 = 5)
- ✅ Scrap Location column shows correctly
- ✅ Other Location column shows correctly

---

### ✅ Test 3: Return Report Timezone

**Objective**: Verify return report dates also use user timezone

**Steps**:
1. Create a customer return (if not exists)
2. Note the date/time in Odoo UI
3. Generate Return Report
4. **Verify**: Date in Excel matches Odoo UI

---

### ✅ Test 4: Filtering with Bidirectional Tracking

**Objective**: Verify filters work correctly with both movement directions

**Test Scenarios**:

**A. Filter by Scrap Location**:
1. Have multiple scrap locations: `WH1/Scrap`, `WH2/Scrap`
2. Create movements to/from both
3. Filter report by `WH1/Scrap` only
4. **Verify**: Only movements involving `WH1/Scrap` appear (both directions)

**B. Filter by Warehouse**:
1. Have movements in `Warehouse 1` and `Warehouse 2`
2. Filter by `Warehouse 1`
3. **Verify**: Only movements within `Warehouse 1` appear

**C. Filter by Product**:
1. Select specific product(s)
2. **Verify**: Only selected products appear in report

---

## Common Test Cases

### Test Case 1: Mistaken Scrap (Full Return)

**Scenario**: Item scrapped by mistake, then fully returned

```
Action 1: Scrap 10 units
  FROM: VWH/Stock/Shelf-A
  TO:   VWH/Scrap
  Result: +10.0 in report

Action 2: Return 10 units
  FROM: VWH/Scrap
  TO:   VWH/Stock/Shelf-A
  Result: -10.0 in report

Net: 0 units in scrap ✅
```

---

### Test Case 2: Partial Return

**Scenario**: Some scrapped items are salvaged

```
Action 1: Scrap 20 units
  Result: +20.0

Action 2: Return 8 units (salvaged)
  Result: -8.0

Net: 12 units remain scrapped ✅
```

---

### Test Case 3: Multiple Scrap Locations

**Scenario**: Items moved between different scrap types

```
Action 1: Scrap 15 units to General Scrap
  FROM: Stock → VWH/Scrap/General
  Result: +15.0 (Scrap Location: VWH/Scrap/General)

Action 2: Move 5 units to Quality Scrap
  FROM: VWH/Scrap/General → VWH/Scrap/Quality
  Result: -5.0 (Scrap Location: VWH/Scrap/General)
          +5.0 (Scrap Location: VWH/Scrap/Quality)

Net in General: 10 units
Net in Quality: 5 units
```

---

## Troubleshooting

### Issue: Dates still showing UTC

**Solution**:
1. Check user timezone is set: Settings → Users → [Your User] → Preferences
2. Verify pytz is installed: `pip3 list | grep pytz`
3. Check Odoo logs for timezone-related errors
4. Restart Odoo after setting timezone

---

### Issue: Returns not showing in report

**Check**:
1. Is the location marked as scrap? `location.scrap_location = True`
2. Is the movement within the selected date range?
3. Is the movement validated (state = 'done')?
4. Check warehouse filter - returns must have destination in warehouse

---

### Issue: Wrong quantities

**Verify**:
1. Scrap-OUT movements are positive ✅
2. Return-FROM-scrap movements are negative ✅
3. Check `location_id` vs `location_dest_id` in movements

---

## SQL Queries for Manual Verification

### Check stock moves to/from scrap:

```sql
-- Moves TO scrap (should be positive in report)
SELECT 
    sm.date,
    pt.name as product,
    sm.product_uom_qty,
    sl_src.complete_name as from_location,
    sl_dest.complete_name as to_location
FROM stock_move sm
JOIN product_product pp ON sm.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
JOIN stock_location sl_src ON sm.location_id = sl_src.id
JOIN stock_location sl_dest ON sm.location_dest_id = sl_dest.id
WHERE sl_dest.scrap_location = TRUE
  AND sm.state = 'done'
  AND sm.date >= '2025-10-01'
ORDER BY sm.date DESC;

-- Moves FROM scrap (should be negative in report)
SELECT 
    sm.date,
    pt.name as product,
    sm.product_uom_qty as qty_in_move,
    sm.product_uom_qty * -1 as qty_in_report,
    sl_src.complete_name as from_location,
    sl_dest.complete_name as to_location
FROM stock_move sm
JOIN product_product pp ON sm.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
JOIN stock_location sl_src ON sm.location_id = sl_src.id
JOIN stock_location sl_dest ON sm.location_dest_id = sl_dest.id
WHERE sl_src.scrap_location = TRUE
  AND sm.state = 'done'
  AND sm.date >= '2025-10-01'
ORDER BY sm.date DESC;
```

---

## Performance Notes

- Reports with large date ranges may take longer to generate (two queries per report)
- Consider adding indexes if performance is an issue:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_stock_move_location_dest_scrap 
    ON stock_move(location_dest_id) 
    WHERE state = 'done';
  
  CREATE INDEX IF NOT EXISTS idx_stock_move_location_src_scrap 
    ON stock_move(location_id) 
    WHERE state = 'done';
  ```

---

## Success Criteria

✅ All tests pass
✅ Dates match Odoo UI exactly
✅ Both scrap-out and returns appear
✅ Quantities are correct (positive/negative)
✅ New columns display properly
✅ Filters work as expected
✅ No errors in Odoo logs

---

## Support

If issues persist:
1. Check module version and ensure latest code is deployed
2. Review Odoo logs: `tail -f /var/log/odoo/odoo-server.log`
3. Verify database integrity
4. Test with a simple product and location first
5. Contact development team with specific error messages
