# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime
import pytz


class ScrapReportXlsx(models.AbstractModel):
    _name = 'report.stock_inventory_reports.scrap_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Scrap Report XLSX'

    def generate_xlsx_report(self, workbook, data, objects):
        """Generate Excel report for scrap data"""
        
        # Get wizard object (first object in objects)
        wizard = objects[0] if objects else None
        if not wizard:
            return
        
        # Get user timezone
        user_tz = self.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)
        
        # Get report data from wizard
        report_data = wizard._get_report_data()
        
        # Create worksheet
        worksheet = workbook.add_worksheet('Scrap Report')
        
        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'bg_color': '#667eea',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
        })
        
        filter_label_format = workbook.add_format({
            'bold': True,
            'bg_color': '#e8e8e8',
            'border': 1,
            'align': 'right',
        })
        
        filter_value_format = workbook.add_format({
            'bg_color': '#f8f8f8',
            'border': 1,
            'text_wrap': True,
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })
        
        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd hh:mm:ss',
            'border': 1,
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'valign': 'top',
            'text_wrap': True,
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
        })
        
        # Set column widths
        worksheet.set_column('A:A', 20)  # Date
        worksheet.set_column('B:B', 30)  # Product Name
        worksheet.set_column('C:C', 15)  # Product Reference
        worksheet.set_column('D:D', 20)  # Operation Type
        worksheet.set_column('E:E', 12)  # Quantity
        worksheet.set_column('F:F', 12)  # Unit of Measure
        worksheet.set_column('G:G', 30)  # Scrap Location
        worksheet.set_column('H:H', 30)  # Other Location
        worksheet.set_column('I:I', 25)  # Reason
        worksheet.set_column('J:J', 30)  # Remarks
        
        current_row = 0
        
        # Write report title
        worksheet.merge_range(current_row, 0, current_row, 9, 'Scrap Report', title_format)
        current_row += 1
        
        # Write filter summary
        worksheet.write(current_row, 0, 'Date Range:', filter_label_format)
        worksheet.merge_range(current_row, 1, current_row, 9, 
                            f"{wizard.date_from.strftime('%Y-%m-%d')} to {wizard.date_to.strftime('%Y-%m-%d')}", 
                            filter_value_format)
        current_row += 1
        
        worksheet.write(current_row, 0, 'Warehouses:', filter_label_format)
        warehouse_names = ', '.join(wizard.warehouse_ids.mapped('name')) or 'All'
        worksheet.merge_range(current_row, 1, current_row, 9, warehouse_names, filter_value_format)
        current_row += 1
        
        if wizard.location_ids:
            worksheet.write(current_row, 0, 'Scrap Locations:', filter_label_format)
            location_names = ', '.join(wizard.location_ids.mapped('complete_name'))
            worksheet.merge_range(current_row, 1, current_row, 9, location_names, filter_value_format)
            current_row += 1
        
        if wizard.operation_type_ids:
            worksheet.write(current_row, 0, 'Operation Types:', filter_label_format)
            operation_names = ', '.join(wizard.operation_type_ids.mapped('name'))
            worksheet.merge_range(current_row, 1, current_row, 9, operation_names, filter_value_format)
            current_row += 1
        
        if wizard.category_ids:
            worksheet.write(current_row, 0, 'Categories:', filter_label_format)
            category_names = ', '.join(wizard.category_ids.mapped('complete_name'))
            worksheet.merge_range(current_row, 1, current_row, 9, category_names, filter_value_format)
            current_row += 1
        
        if wizard.product_ids:
            worksheet.write(current_row, 0, 'Products:', filter_label_format)
            product_names = ', '.join(wizard.product_ids.mapped('display_name')[:10])  # Limit to first 10
            if len(wizard.product_ids) > 10:
                product_names += f' ... and {len(wizard.product_ids) - 10} more'
            worksheet.merge_range(current_row, 1, current_row, 9, product_names, filter_value_format)
            current_row += 1
        
        # Add blank row before data table
        current_row += 1
        
        # Write column headers
        headers = [
            'Date',
            'Product Name',
            'Product Reference',
            'Operation Type',
            'Quantity',
            'Unit of Measure',
            'Scrap Location',
            'Location',
            'Reason',
            'Remarks',
        ]
        
        header_row = current_row
        for col, header in enumerate(headers):
            worksheet.write(current_row, col, header, header_format)
        current_row += 1
        
        # Write data
        for line in report_data:
            # Convert UTC datetime to user timezone
            date_utc = line['date']
            if isinstance(date_utc, str):
                date_utc = fields.Datetime.from_string(date_utc)
            
            # Convert from UTC to user timezone
            date_utc = pytz.UTC.localize(date_utc) if date_utc.tzinfo is None else date_utc
            date_local = date_utc.astimezone(tz)
            # Remove timezone info for Excel (Excel doesn't store timezone)
            date_naive = date_local.replace(tzinfo=None)
            
            worksheet.write_datetime(current_row, 0, date_naive, date_format)
            worksheet.write(current_row, 1, line['product_name'], cell_format)
            worksheet.write(current_row, 2, line['product_reference'], cell_format)
            worksheet.write(current_row, 3, line['operation_type'], cell_format)
            worksheet.write(current_row, 4, line['quantity'], number_format)
            worksheet.write(current_row, 5, line['uom'], cell_format)
            worksheet.write(current_row, 6, line['scrap_location'], cell_format)
            worksheet.write(current_row, 7, line['other_location'], cell_format)
            worksheet.write(current_row, 8, line['reason'], cell_format)
            worksheet.write(current_row, 9, line['remarks'], cell_format)
            current_row += 1
        
        # Freeze panes: Freeze header row
        worksheet.freeze_panes(header_row + 1, 0)
