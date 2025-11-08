# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReturnReportWizard(models.TransientModel):
    """Wizard to generate Return Report"""
    _name = 'return.report.wizard'
    _description = 'Return Report Wizard'

    _inherit = [
        'base.date.range.wizard',
        'base.warehouse.wizard',
        'base.location.wizard',
        'base.operation.type.wizard',
        'base.product.categ.wizard'
    ]
    
    salesman_ids = fields.Many2many(
        'hr.employee',
        string='Salesperson',
        help='Select specific salespeople to filter the report. Leave empty to include all.'
    )
    operation_type_ids_domain = fields.Binary(
        string='Operation Type Domain',
        compute='_compute_operation_type_ids_domain'
    )

    @api.depends('warehouse_ids')
    def _compute_operation_type_ids_domain(self):
        """Compute domain to show only operation types with scrap destination"""
        for wizard in self:
            # Find all scrap locations
            # return_locations = self.env['stock.location'].search([('return_location', '=', True)])

            warehouse_ids = wizard.warehouse_ids.ids

            # domain = [('default_location_dest_id', 'in', return_locations.ids)]
            domain = []
            if warehouse_ids:
                domain.append(('warehouse_id', 'in', warehouse_ids))

            wizard.operation_type_ids_domain = domain

    def _get_report_data(self):
        """Get return report data based on filters"""
        self.ensure_one()
        
        # Build domain for stock moves with customer returns
        domain = self._get_date_domain('date')
        domain.extend([
            ('picking_id.picking_kind', '=', 'customer_return'),
            ('state', '=', 'done'),
        ])
        
        # Filter by warehouse
        warehouse_location_ids = self._get_warehouse_location_ids()
        if warehouse_location_ids:
            domain.append(('location_dest_id', 'in', warehouse_location_ids))
        
        # Filter by specific locations
        if self.location_ids:
            domain.append(('location_dest_id', 'in', self.location_ids.ids))
        
        # Filter by operation type
        if self.operation_type_ids:
            domain.append(('picking_id.picking_type_id', 'in', self.operation_type_ids.ids))
        
        # Filter by product using base wizard method
        products = self._fetch_products_from_wizard()
        if products:
            domain.append(('product_id', 'in', products.ids))
        
        # Search for stock moves
        stock_moves = self.env['stock.move'].search(domain, order='date desc')
        
        # Prepare report data
        report_lines = []
        for move in stock_moves:
            # Get sale order line
            sale_line = move.sale_line_id
            if not sale_line:
                # Try to find from origin or other relations
                if move.origin_returned_move_id and move.origin_returned_move_id.sale_line_id:
                    sale_line = move.origin_returned_move_id.sale_line_id
            
            # Get salesperson (employee)
            salesperson_name = ''

            employee = None
            if sale_line and sale_line.order_id and sale_line.order_id.employee_id:
                employee = sale_line.order_id.employee_id
                # Filter by salesperson if specified
                if self.salesman_ids and employee.id not in self.salesman_ids.ids:
                    continue
                salesperson_name = employee.name
            elif self.salesman_ids:
                # Skip if salesperson filter is set but no salesperson found
                continue
            
            # Get return invoice
            invoice_number = ''
            if move.picking_id and move.picking_id.sale_id:
                invoices = move.picking_id.sale_id.invoice_ids.filtered(
                    lambda inv: inv.state == 'posted' and inv.move_type == 'out_refund'
                )
                if invoices:
                    invoice_number = ', '.join(invoices.mapped('name'))
            
            # Get customer name
            customer_name = ''
            if move.picking_id and move.picking_id.partner_id:
                customer_name = move.picking_id.partner_id.name
            elif sale_line and sale_line.order_id:
                customer_name = sale_line.order_id.partner_id.name
            
            # Get return reason from sale order line
            return_reason = ''
            order_name = ''
            if sale_line:
                # Safely get return_reason field if it exists
                return_reason = sale_line.return_reason and sale_line.return_reason.name or ''
                order_name = sale_line.order_id.name or ''
            
            # Get received by (user who validated the picking)
            received_by = ''
            if move.picking_id:
                received_by = move.picking_id.user_id.name or move.picking_id.write_uid.name
            
            report_lines.append({
                'date': move.date,
                'invoice_number': invoice_number,
                'order_number': order_name,
                'customer_name': customer_name,
                'product_name': move.product_id.display_name,
                'product_reference': move.product_id.default_code or '',
                'quantity': move.product_uom_qty,
                'salesperson': salesperson_name,
                'return_reason': return_reason,
                'received_by': received_by,
            })
        
        return report_lines

    def action_generate_report(self):
        """Generate and download the return report"""
        self.ensure_one()
        return self.env.ref('stock_inventory_reports.action_return_report_xlsx').report_action(self, {})
