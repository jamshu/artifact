# Deployment Guide - XLSX Report Refactoring

## Prerequisites

1. **Odoo 16** installed and running
2. **report_xlsx module** available in your Odoo installation
   - Check if installed: Search for "report_xlsx" in Apps
   - If not installed: Install from Odoo Apps or add to your addons path
3. **xlsxwriter Python package** installed
   ```bash
   pip3 install xlsxwriter
   ```

## Deployment Steps

### Step 1: Backup (Optional but Recommended)
```bash
# Backup your database
pg_dump your_database_name > backup_$(date +%Y%m%d).sql

# Backup the module directory
cp -r addons-stock/stock_inventory_reports addons-stock/stock_inventory_reports.backup
```

### Step 2: Stop Odoo Service (if running)
```bash
# If running as a service
sudo systemctl stop odoo

# Or if running manually, stop the Odoo process
```

### Step 3: Verify Module Files
Ensure all new files are in place:
```bash
cd /Users/jamshid/PycharmProjects/Siafa/odoo16e_simc/addons-stock/stock_inventory_reports

# Check new files exist
ls -la reports/
ls -la data/

# Should show:
# reports/__init__.py
# reports/scrap_report_xlsx.py
# reports/return_report_xlsx.py
# data/report_actions.xml
```

### Step 4: Update Module Permissions (if needed)
```bash
# Ensure proper ownership
sudo chown -R odoo:odoo /path/to/addons-stock/stock_inventory_reports

# Ensure proper permissions
sudo chmod -R 755 /path/to/addons-stock/stock_inventory_reports
```

### Step 5: Install/Check report_xlsx Module

**Option A: Via Odoo UI (Recommended)**
1. Start Odoo
2. Go to Apps menu
3. Remove "Apps" filter
4. Search for "report_xlsx"
5. If not installed, click "Install"

**Option B: Via Command Line**
```bash
odoo-bin -d your_database -i report_xlsx --stop-after-init
```

### Step 6: Upgrade the stock_inventory_reports Module

**Option A: Via Odoo UI (Recommended)**
1. Go to Apps menu
2. Remove "Apps" filter
3. Search for "Stock Inventory Reports"
4. Click on the module
5. Click "Upgrade" button

**Option B: Via Command Line**
```bash
odoo-bin -d your_database -u stock_inventory_reports --stop-after-init
```

### Step 7: Restart Odoo
```bash
# If running as a service
sudo systemctl start odoo

# Monitor logs
tail -f /var/log/odoo/odoo-server.log

# Or if running manually
./odoo-bin -c /path/to/odoo.conf
```

### Step 8: Clear Browser Cache
- Clear browser cache or use Ctrl+Shift+R / Cmd+Shift+R
- This ensures new JavaScript and CSS are loaded

## Verification Steps

### 1. Check Module Status
```sql
-- Connect to PostgreSQL
psql your_database_name

-- Check module state
SELECT name, state, latest_version 
FROM ir_module_module 
WHERE name IN ('stock_inventory_reports', 'report_xlsx');

-- Should show both modules as 'installed'
```

### 2. Check Report Actions
```sql
-- Check if report actions were created
SELECT id, name, model, report_type, report_name 
FROM ir_act_report 
WHERE report_name LIKE '%stock_inventory_reports%';

-- Should show:
-- action_scrap_report_xlsx
-- action_return_report_xlsx
```

### 3. Test Scrap Report
1. Navigate to **Inventory → Reporting → Scrap Report**
2. Select date range
3. Select at least one warehouse
4. Click "Generate Report"
5. Verify:
   - ✅ Excel file downloads immediately
   - ✅ No error messages
   - ✅ Report contains correct data
   - ✅ Formatting looks correct

### 4. Test Return Report
1. Navigate to **Inventory → Reporting → Return Report**
2. Select date range
3. Select at least one warehouse
4. Click "Generate Report"
5. Verify:
   - ✅ Excel file downloads immediately
   - ✅ No error messages
   - ✅ Report contains correct data
   - ✅ Formatting looks correct

### 5. Test Filter Functionality
**Scrap Report**:
- Test warehouse filtering
- Test scrap location filtering (should only show scrap locations)
- Test scrap operation type filtering
- Test product/category filtering

**Return Report**:
- Test warehouse filtering
- Test location filtering
- Test operation type filtering
- Test salesperson filtering
- Test product/category filtering

## Troubleshooting

### Issue: "Module report_xlsx not found"
**Solution**: Install the report_xlsx module
```bash
# Download if not available
cd /path/to/odoo/addons
git clone https://github.com/OCA/reporting-engine.git -b 16.0
# Or download the specific module

# Install
odoo-bin -d your_database -i report_xlsx --stop-after-init
```

### Issue: "ImportError: No module named 'xlsxwriter'"
**Solution**: Install xlsxwriter Python package
```bash
pip3 install xlsxwriter
# Or for specific Odoo user
sudo -u odoo pip3 install xlsxwriter
```

### Issue: "Report not generating" or "No action found"
**Solution**: Upgrade the module properly
```bash
# Force upgrade with assets
odoo-bin -d your_database -u stock_inventory_reports --stop-after-init

# If still not working, try updating base
odoo-bin -d your_database -u base,stock_inventory_reports --stop-after-init
```

### Issue: "Server Error: External ID not found"
**Solution**: Check XML file was loaded
```sql
-- Check if report actions exist
SELECT * FROM ir_act_report 
WHERE report_name LIKE '%stock_inventory_reports%';

-- Check external IDs
SELECT * FROM ir_model_data 
WHERE module = 'stock_inventory_reports' 
AND name LIKE '%action%report%';
```

If not found, the XML file wasn't loaded. Check:
- XML file exists in `data/report_actions.xml`
- XML file is listed in `__manifest__.py` data section
- XML file is valid (no syntax errors)

### Issue: "Wizard freezes after clicking Generate"
**Solution**: This should be fixed with the refactoring. If it still happens:
1. Check browser console for JavaScript errors
2. Check Odoo logs for Python errors
3. Verify report class is properly registered
4. Try clearing Odoo cache: `odoo-bin -d your_database --stop-after-init`

### Issue: "Excel file is empty or has no data"
**Solution**: 
1. Check `_get_report_data()` method returns data
2. Verify filters are not too restrictive
3. Check stock moves exist for the selected period
4. Review Odoo logs for any errors during data fetching

## Rollback Plan

If issues occur and you need to rollback:

### Step 1: Restore from Backup
```bash
# Stop Odoo
sudo systemctl stop odoo

# Restore database
psql your_database_name < backup_YYYYMMDD.sql

# Restore module files
rm -rf addons-stock/stock_inventory_reports
mv addons-stock/stock_inventory_reports.backup addons-stock/stock_inventory_reports

# Restart Odoo
sudo systemctl start odoo
```

### Step 2: Downgrade Module (Alternative)
If you have the old code in version control:
```bash
cd addons-stock/stock_inventory_reports
git checkout <previous_commit_hash>

# Restart Odoo with module upgrade
odoo-bin -d your_database -u stock_inventory_reports --stop-after-init
```

## Post-Deployment Monitoring

### Monitor Odoo Logs
```bash
tail -f /var/log/odoo/odoo-server.log | grep -i "stock_inventory_reports\|scrap\|return"
```

### Monitor Performance
- Check report generation time
- Monitor memory usage during report generation
- Check for any error patterns in logs

### User Feedback
- Collect feedback from users
- Document any issues or improvements needed
- Monitor support tickets related to reports

## Success Criteria

✅ Module upgrades without errors
✅ Both report_xlsx and stock_inventory_reports show as installed
✅ Report actions visible in database
✅ Scrap report generates and downloads correctly
✅ Return report generates and downloads correctly
✅ All filters work as expected
✅ Excel formatting is correct
✅ No performance degradation
✅ No errors in Odoo logs

## Support Contacts

- **Technical Issues**: [Your Technical Contact]
- **User Issues**: [Your Support Contact]
- **Documentation**: See `REFACTORING_XLSX_REPORTS.md`

---

**Deployment Date**: ___________
**Deployed By**: ___________
**Verified By**: ___________
**Notes**: ___________
