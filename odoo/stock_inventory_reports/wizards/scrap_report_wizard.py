# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ScrapReportWizard(models.TransientModel):
    """Wizard to generate Scrap Report"""
    _name = 'scrap.report.wizard'
    _description = 'Scrap Report Wizard'
    _inherit = [
        'base.date.range.wizard',
        'base.warehouse.wizard',
        'base.location.wizard',
        'base.operation.type.wizard',
        'base.product.categ.wizard'
    ]
    
    # Computed domains for scrap-specific filtering
    location_ids_domain = fields.Binary(
        string='Location Domain',
        compute='_compute_location_ids_domain'
    )
    
    operation_type_ids_domain = fields.Binary(
        string='Operation Type Domain',
        compute='_compute_operation_type_ids_domain'
    )

    @api.depends('warehouse_ids')
    def _compute_location_ids_domain(self):
        """Compute domain to show only scrap locations"""
        for wizard in self:
            domain = [('scrap_location', '=', True)]
            wizard.location_ids_domain = domain
    
    @api.depends('warehouse_ids')
    def _compute_operation_type_ids_domain(self):
        """Compute domain to show only operation types with scrap destination"""
        for wizard in self:
            # Find all scrap locations
            scrap_locations = self.env['stock.location'].search([('scrap_location', '=', True)])
            warehouse_ids = wizard.warehouse_ids.ids
            scrap_location_ids = scrap_locations.ids
            domain = [('default_location_dest_id', 'in', scrap_location_ids)]
            if warehouse_ids:
                domain.append(('warehouse_id', 'in', warehouse_ids))

            wizard.operation_type_ids_domain = domain


    def _get_report_data(self):
        """Get scrap report data based on filters"""
        self.ensure_one()
        
        # Find scrap locations
        # scrap_locations = self.env['stock.location'].search([('scrap_location', '=', True)])
        #
        # if not scrap_locations:
        #     return []

        # Build domain for stock moves
        domain = self._get_date_domain('date')
        domain.extend([
            ('state', '=', 'done'),
        ])
        
        # Filter by warehouse (check if source location belongs to warehouse)
        warehouse_location_ids = self._get_warehouse_location_ids()
        if warehouse_location_ids:
            domain.append(('location_id', 'in', warehouse_location_ids))
        
        # Filter by specific locations
        if self.location_ids:
            domain.append(('location_dest_id', 'in', self.location_ids.ids))
        
        # Filter by operation type
        # If no operation type selected, use all scrap operation types
        if self.operation_type_ids:
            operation_type_ids = self.operation_type_ids.ids
        else:
            # Get all operation types with scrap destination
            scrap_locations = self.env['stock.location'].search([('scrap_location', '=', True)])
            scrap_operation_types = self.env['stock.picking.type'].search([
                ('default_location_dest_id', 'in', scrap_locations.ids)
            ])
            operation_type_ids = scrap_operation_types.ids
        
        if operation_type_ids:
            domain.append(('picking_id.picking_type_id', 'in', operation_type_ids))
        
        # Filter by product using base wizard method
        products = self._fetch_products_from_wizard()
        if products:
            domain.append(('product_id', 'in', products.ids))
        
        # Search for stock moves
        stock_moves = self.env['stock.move'].search(domain, order='date desc')
        
        # Prepare report data
        report_lines = []
        for move in stock_moves:
            report_lines.append({
                'date': move.date,
                'product_name': move.product_id.display_name,
                'product_reference': move.product_id.default_code or '',
                'operation_type': move.picking_id.picking_type_id.name if move.picking_id else '',
                'quantity': move.product_uom_qty,
                'uom': move.product_uom.name,
                'reason': move.picking_id.origin or '',
                'remarks': move.picking_id.note or '',
            })
        
        return report_lines

    def action_generate_report(self):
        """Generate and download the scrap report"""
        self.ensure_one()
        return self.env.ref('stock_inventory_reports.action_scrap_report_xlsx').report_action(self, {})
