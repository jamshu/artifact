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
        """Get scrap report data based on filters
        
        This method retrieves moves involving scrap locations:
        - Moves TO scrap locations (scrapped items): shown as positive quantity
        - Moves FROM scrap locations (returned items): shown as negative quantity
        """
        self.ensure_one()
        
        # Get all scrap locations or filtered scrap locations
        if self.location_ids:
            scrap_locations = self.location_ids
        else:
            scrap_locations = self.env['stock.location'].search([('scrap_location', '=', True)])
        
        if not scrap_locations:
            return []
        
        scrap_location_ids = scrap_locations.ids
        
        # Base domain for stock moves
        base_domain = self._get_date_domain('date')
        base_domain.extend([
            ('state', '=', 'done'),
        ])
        
        # Filter by product using base wizard method
        products = self._fetch_products_from_wizard()
        if products:
            base_domain.append(('product_id', 'in', products.ids))
        
        # Get warehouse locations for filtering
        warehouse_location_ids = self._get_warehouse_location_ids()
        
        report_lines = []
        
        # === 1. Get moves TO scrap locations (scrapped items - positive quantity) ===
        to_scrap_domain = base_domain.copy()
        to_scrap_domain.append(('location_dest_id', 'in', scrap_location_ids))
        
        # Filter by warehouse: source location should be in warehouse
        if warehouse_location_ids:
            to_scrap_domain.append(('location_id', 'in', warehouse_location_ids))
        
        # Filter by operation type
        if self.operation_type_ids:
            to_scrap_domain.append(('picking_id.picking_type_id', 'in', self.operation_type_ids.ids))
        
        to_scrap_moves = self.env['stock.move'].search(to_scrap_domain)
        
        for move in to_scrap_moves:
            report_lines.append({
                'date': move.date,
                'product_name': move.product_id.display_name,
                'product_reference': move.product_id.default_code or '',
                'operation_type': move.picking_id.picking_type_id.name if move.picking_id else '',
                'quantity': move.product_uom_qty,  # Positive: items scrapped
                'uom': move.product_uom.name,
                'reason': move.picking_id.origin or '',
                'remarks': move.picking_id.note or '',
                'scrap_location': move.location_dest_id.complete_name,
                'other_location': move.location_id.complete_name,
            })
        
        # === 2. Get moves FROM scrap locations (returned items - negative quantity) ===
        from_scrap_domain = base_domain.copy()
        from_scrap_domain.append(('location_id', 'in', scrap_location_ids))
        
        # Filter by warehouse: destination location should be in warehouse
        if warehouse_location_ids:
            from_scrap_domain.append(('location_dest_id', 'in', warehouse_location_ids))
        
        # Filter by operation type
        if self.operation_type_ids:
            from_scrap_domain.append(('picking_id.picking_type_id', 'in', self.operation_type_ids.ids))
        
        from_scrap_moves = self.env['stock.move'].search(from_scrap_domain)
        
        for move in from_scrap_moves:
            report_lines.append({
                'date': move.date,
                'product_name': move.product_id.display_name,
                'product_reference': move.product_id.default_code or '',
                'operation_type': move.picking_id.picking_type_id.name if move.picking_id else '',
                'quantity': -move.product_uom_qty,  # Negative: items returned from scrap
                'uom': move.product_uom.name,
                'reason': move.picking_id.origin or '',
                'remarks': move.picking_id.note or '',
                'scrap_location': move.location_id.complete_name,
                'other_location': move.location_dest_id.complete_name,
            })
        
        # Sort by date descending
        report_lines.sort(key=lambda x: x['date'], reverse=True)
        
        return report_lines

    def action_generate_report(self):
        """Generate and download the scrap report"""
        self.ensure_one()
        return self.env.ref('stock_inventory_reports.action_scrap_report_xlsx').report_action(self, {})
