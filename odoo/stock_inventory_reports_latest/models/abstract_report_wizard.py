# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BaseDateRangeWizard(models.AbstractModel):
    """Abstract model for date range selection in wizards"""
    _name = 'base.date.range.wizard'
    _description = 'Base Date Range Wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Validate date range"""
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise ValidationError(_('Date From cannot be later than Date To.'))

    def _get_date_domain(self, field_name='date'):
        """Build date range domain for filtering"""
        self.ensure_one()
        return [
            (field_name, '>=', fields.Datetime.to_datetime(self.date_from)),
            (field_name, '<=', fields.Datetime.to_datetime(self.date_to)),
        ]


class BaseExcelReportWizard(models.AbstractModel):
    """Abstract model for Excel file download in wizards"""
    _name = 'base.excel.report.wizard'
    _description = 'Base Excel Report Wizard'

    excel_file = fields.Binary(string='Excel File', readonly=True)
    excel_filename = fields.Char(string='Excel Filename', readonly=True)
    
    # This should be overridden in the concrete class
    _report_name = 'Report'

    def action_generate_report(self):
        """Generate and download the report as Excel"""
        self.ensure_one()
        
        try:
            import xlsxwriter
        except ImportError:
            raise ValidationError(_('Please install xlsxwriter Python library to generate Excel reports.'))
        
        # Get report data (must be implemented in concrete class)
        report_data = self._get_report_data()
        
        if not report_data:
            raise ValidationError(_('No data found for the selected filters.'))
        
        # Generate Excel file (must be implemented in concrete class)
        excel_file = self._generate_excel_report(report_data)
        
        # Get filename
        filename = self._get_report_filename()
        
        # Save the file
        self.write({
            'excel_file': excel_file,
            'excel_filename': filename,
        })
        
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
    
    def _get_report_filename(self):
        """Generate report filename. Can be overridden in concrete class."""
        date_from = getattr(self, 'date_from', False)
        date_to = getattr(self, 'date_to', False)
        
        if date_from and date_to:
            return f'{self._report_name}_{date_from}_{date_to}.xlsx'
        return f'{self._report_name}.xlsx'
    
    def _get_report_data(self):
        """Get report data. Must be implemented in concrete class."""
        raise NotImplementedError('Method _get_report_data must be implemented in concrete class')
    
    def _generate_excel_report(self, report_data):
        """Generate Excel file from report data. Must be implemented in concrete class."""
        raise NotImplementedError('Method _generate_excel_report must be implemented in concrete class')
    
    def _get_excel_header_format(self, workbook):
        """Get standard header format for Excel reports"""
        return workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })
    
    def _get_excel_date_format(self, workbook):
        """Get standard date format for Excel reports"""
        return workbook.add_format({
            'num_format': 'yyyy-mm-dd hh:mm:ss',
            'border': 1,
        })
    
    def _get_excel_cell_format(self, workbook):
        """Get standard cell format for Excel reports"""
        return workbook.add_format({
            'border': 1,
            'valign': 'top',
            'text_wrap': True,
        })
    
    def _get_excel_number_format(self, workbook):
        """Get standard number format for Excel reports"""
        return workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
        })


class BaseWarehouseWizard(models.AbstractModel):
    """Abstract model for warehouse selection in wizards"""
    _name = 'base.warehouse.wizard'
    _description = 'Base Warehouse Wizard'

    warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Warehouses',
        required=True,
        help='Select one or more warehouses to filter the report'
    )

    def _get_warehouse_location_ids(self):
        """Get all location IDs for selected warehouses"""
        self.ensure_one()
        location_ids = []
        for warehouse in self.warehouse_ids:
            if warehouse.view_location_id:
                locations = self.env['stock.location'].search([
                    ('id', 'child_of', warehouse.view_location_id.id)
                ])
                location_ids.extend(locations.ids)
        return location_ids


class BaseLocationWizard(models.AbstractModel):
    """Abstract model for location selection in wizards"""
    _name = 'base.location.wizard'
    _description = 'Base Location Wizard'

    location_ids = fields.Many2many(
        'stock.location',
        string='Locations',
        help='Select specific locations to filter the report. Leave empty to include all locations.'
    )


class BaseOperationTypeWizard(models.AbstractModel):
    """Abstract model for operation type selection in wizards"""
    _name = 'base.operation.type.wizard'
    _description = 'Base Operation Type Wizard'

    operation_type_ids = fields.Many2many(
        'stock.picking.type',
        string='Operation Types',
        help='Select specific operation types to filter the report. Leave empty to include all types.'
    )
