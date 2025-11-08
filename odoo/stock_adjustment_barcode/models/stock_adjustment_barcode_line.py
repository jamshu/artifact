# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round


class StockAdjustmentBarcodeLine(models.Model):
    _name = 'stock.adjustment.barcode.line'
    _description = 'Stock Adjustment Barcode Line'

    is_editable = fields.Boolean(
        default=False,
        copy=False,
        string="Has Error"
    )

    unit_price = fields.Float(
        compute='_compute_product_qty',
        store=True,
        string="Unit Price (valuation layer)",
        help="This price will used on cost Analysis Report",
    )

    forecast_qty = fields.Float(
        compute='_compute_product_qty',
        store=True
    )

    on_hand_qty = fields.Float(
        compute='_compute_product_qty',
        store=True
    )

    difference_qty = fields.Float(
        compute='_compute_difference_qty',
        store=True
    )

    total_scanned_qty = fields.Float(
        compute='_compute_product_qty',
        store=True
    )

    product_id = fields.Many2one(comodel_name='product.product')

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id)]"
    )

    company_id = fields.Many2one('res.company', 'Company', related='inv_adjustment_id.company_id', readonly=True, store=True)

    inv_adjustment_id = fields.Many2one(
        comodel_name='stock.adjustment.barcode',
        required=True,
        ondelete='cascade'
    )

    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Product UoM',
        related='product_id.uom_id'
    )

    adjustment_line_info_ids = fields.One2many(
        comodel_name='stock.adjustment.barcode.line.info',
        inverse_name='inv_adjustment_line_id',
        copy=False
    )

    adjustment_line_lot_ids = fields.One2many(
        comodel_name='stock.adjustment.barcode.lot.line',
        inverse_name='inv_adjustment_line_id',
        copy=False
    )

    stock_move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='inv_adjustment_line_id',
        copy=False
    )

    parent_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Main Product',
        help='The parent product from BOM transfer when this line is consolidated from child products'
    )

    is_parent_line = fields.Boolean(
        string='Is Parent Line',
        compute='_compute_is_parent_line',
        store=True,
        help='Indicates if this line is a parent that consolidates child products from BOM transfer'
    )

    is_child_line = fields.Boolean(
        string='Is Child Line',
        compute='_compute_is_child_line',
        store=True,
        help='Indicates if this line is a child line that gets consolidated to a parent product'
    )

    display_sequence = fields.Integer(
        string='Display Sequence',
        default=lambda self: self._get_default_display_sequence(),
        store=True,
        help='Sequence for displaying parent lines before child lines'
    )

    display_name_with_relation = fields.Char(
        string='Product Display Name',
        compute='_compute_display_name_with_relation',
        help='Product name with parent-child relationship indicator'
    )

    _sql_constraints = [(
        'unique_product',
        'UNIQUE(product_id, lot_id, inv_adjustment_id)',
        'Product and Lot number should be uniq on lines')]

    @api.depends('parent_product_id')
    def _compute_is_parent_line(self):
        """Compute if this line is a parent line that consolidates child products."""
        for record in self:
            # Check if there are other lines with this product as parent_product_id
            child_lines_count = self.search_count([
                ('inv_adjustment_id', '=', record.inv_adjustment_id.id),
                ('parent_product_id', '=', record.product_id.id),
                ('id', '!=', record.id)
            ])
            record.is_parent_line = child_lines_count > 0

    @api.depends('parent_product_id')
    def _compute_is_child_line(self):
        """Compute if this line is a child line that gets consolidated to a parent."""
        for record in self:
            record.is_child_line = bool(record.parent_product_id)

    def _get_default_display_sequence(self):
        """Get default display sequence - called when creating new lines."""
        if self.product_id:
            return 1000000 + (self.product_id.id * 10)
        return 1000000
    
    def _compute_display_sequence(self):
        """Compute display sequence to show parent-child groups first, then regular products."""
        for record in self:
            # Skip if sequence was manually set (during consolidation)
            if record.display_sequence and record.display_sequence < 1000000:
                continue
                
            # Check if this product is a parent by looking for children
            has_children = record.inv_adjustment_id.inv_adjustment_line_ids.filtered(
                lambda l: l.parent_product_id == record.product_id
            )
            
            if record.parent_product_id:
                # Child line - group with parent (base 1000 for parent-child groups)
                # Use parent product ID for grouping, add small offset for child
                record.display_sequence = 1000 + (record.parent_product_id.id * 10) + (record.id % 10)
            elif has_children:
                # Parent line - appears first in its group (base 1000 for parent-child groups)
                record.display_sequence = 1000 + (record.product_id.id * 10)
            else:
                # Regular standalone line - appears after all parent-child groups (base 1000000)
                record.display_sequence = 1000000 + (record.product_id.id * 10)

    @api.depends('product_id', 'parent_product_id', 'is_parent_line', 'is_child_line')
    def _compute_display_name_with_relation(self):
        """Compute display name with parent-child relationship indicator."""
        for record in self:
            if record.parent_product_id:
                # Child line
                record.display_name_with_relation = f"↳ 📦{record.product_id.display_name}"
            elif record.is_parent_line:
                # Parent line
                record.display_name_with_relation = f"💳 {record.product_id.display_name}"
            else:
                # Regular line
                record.display_name_with_relation = record.product_id.display_name

    def _find_parent_product_from_bom_transfer(self):
        """
        Find parent product from BOM transfer type.
        Search for BOM where the scanned product is the main product (product_tmpl_id) 
        and type is 'transfer', then return the first product from bom_line_ids.
        """
        self.ensure_one()
        if not self.product_id:
            return False
            
        # Search for BOMs where this product is the main product and BOM type is 'transfer'
        bom = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('type', '=', 'transfer')
        ], limit=1)
        
        if bom and bom.bom_line_ids:
            # Check if the BOM is applicable to the current warehouse/location
            if bom.warehouse_ids:
                # Get warehouse from location
                location = self.inv_adjustment_id.location_id
                warehouse = location.warehouse_id or location.get_warehouse()
                if warehouse not in bom.warehouse_ids:
                    return False
            
            # Return the first product from bom_line_ids (parent product)
            return bom.bom_line_ids[0].product_id
            
        return False

    def _get_bom_transfer_for_child(self):
        """
        Get the BOM transfer record for this child product.
        Returns the BOM object if found, False otherwise.
        """
        self.ensure_one()
        if not self.product_id:
            return False
            
        # Search for BOMs where this product is the main product and BOM type is 'transfer'
        bom = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('type', '=', 'transfer')
        ], limit=1)
        
        if bom and bom.bom_line_ids:
            # Check if the BOM is applicable to the current warehouse/location
            if bom.warehouse_ids:
                # Get warehouse from location
                location = self.inv_adjustment_id.location_id
                warehouse = location.warehouse_id or location.get_warehouse()
                if warehouse not in bom.warehouse_ids:
                    return False
            return bom
            
        return False

    def _compute_parent_qty_from_children(self, child_lines):
        """
        Compute parent quantity from child lines using BOM conversion ratios.
        For each child product, find its BOM and convert the scanned quantity
        to parent product quantity based on the BOM line ratios.
        
        BOM Transfer Structure:
        ----------------------
        In mrp.bom with type='transfer':
        - product_tmpl_id: Child Product (e.g., Arjoon Mamool 400 gms - No added Sugar)
        - product_qty: Quantity of child product (e.g., 1.0 unit)
        - bom_line_ids: Contains parent product(s)
          - product_id: Parent Product (e.g., Arjoon Mamool Assorted 400 gms 3 in 1)
          - product_qty: Quantity of parent produced (e.g., 3.0 units)
          - product_uom_id: Unit of measure for parent
        
        Conversion Example:
        ------------------
        Scenario: 5 units of "Arjoon Mamool 400 gms - No added Sugar" scanned
        BOM Setup:
          - Child: 1 unit of "Arjoon Mamool 400 gms - No added Sugar"
          - Parent: 3 units of "Arjoon Mamool Assorted 400 gms 3 in 1"
        Conversion: (5 scanned units / 1 BOM unit) * 3 parent units = 15 units
        
        UoM Handling:
        ------------
        If products use different UoMs (e.g., Units vs Grams), the conversion
        handles UoM conversion automatically using Odoo's UoM conversion system.
        """
        self.ensure_one()
        total_parent_qty = 0.0
        
        for child_line in child_lines:
            child_scanned_qty = child_line.total_scanned_qty
            
            # Get the BOM for this child product
            bom = child_line._get_bom_transfer_for_child()
            
            if not bom:
                # If no BOM found, use child qty as-is (shouldn't happen in normal flow)
                total_parent_qty += child_scanned_qty
                continue
            
            # Find the BOM line that points to the parent product (this line's product)
            parent_bom_line = bom.bom_line_ids.filtered(
                lambda l: l.product_id == self.product_id
            )
            
            if not parent_bom_line:
                # If no matching BOM line found, use child qty as-is
                total_parent_qty += child_scanned_qty
                continue
            
            parent_bom_line = parent_bom_line[0]  # Take first match
            
            # Calculate conversion ratio from BOM
            # BOM structure: bom.product_qty of child -> parent_bom_line.product_qty of parent
            bom_product_qty = bom.product_qty or 1.0  # Child quantity in BOM
            parent_line_qty = parent_bom_line.product_qty or 1.0  # Parent quantity in BOM
            
            # Convert scanned child quantity to parent quantity using BOM ratio
            # Formula: (scanned_child_qty / bom_product_qty) * parent_line_qty
            # Example: (5 scanned / 1 BOM child) * 3 BOM parent = 15 parent units
            converted_qty = (child_scanned_qty / bom_product_qty) * parent_line_qty
            
            # Handle Unit of Measure conversions
            child_uom = child_line.product_uom_id  # Child product's UoM
            bom_uom = bom.product_uom_id  # BOM's base UoM
            parent_line_uom = parent_bom_line.product_uom_id  # Parent BOM line's UoM
            parent_uom = self.product_uom_id  # Parent product's UoM
            
            # Step 1: Convert from child UoM to BOM UoM if they differ
            # (e.g., if child is in grams but BOM is in kg)
            if child_uom != bom_uom:
                converted_qty = child_uom._compute_quantity(
                    converted_qty, bom_uom, rounding_method='HALF-UP'
                )
            
            # Step 2: Convert from parent BOM line UoM to actual parent product UoM
            # (e.g., if BOM line is in kg but parent product is in units)
            if parent_line_uom != parent_uom:
                converted_qty = parent_line_uom._compute_quantity(
                    converted_qty, parent_uom, rounding_method='HALF-UP'
                )
            
            total_parent_qty += converted_qty
        
        return total_parent_qty

    @api.depends('lot_id', 'inv_adjustment_id.location_id', 'adjustment_line_info_ids',
                 'adjustment_line_info_ids.product_id', 'adjustment_line_info_ids.scanned_qty',
                 'parent_product_id', 'is_parent_line')
    def _compute_product_qty(self):
        """
        Compute the product quantities based on the stock quants and adjustment details.
        For parent lines, compute total from child lines by converting using BOM ratios.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        quant_obj = self.env['stock.quant'].sudo()
        for record in self:
            product = record.product_id
            domain = [('product_id', '=', product.id), ('location_id', '=', record.inv_adjustment_id.location_id.id)]
            if record.lot_id:
                domain += [('lot_id', '=', record.lot_id.id)]

            product_quants = quant_obj.search(domain)
            on_hand_qty = sum(product_quants.mapped('quantity'))
            
            # Check if this is a parent line (has children)
            child_lines = record.inv_adjustment_id.inv_adjustment_line_ids.filtered(
                lambda l: l.parent_product_id == record.product_id
            )
            
            if child_lines:
                # Parent line - sum up converted quantities from all child lines using BOM ratios
                total_scanned_qty = record._compute_parent_qty_from_children(child_lines)
            else:
                # Regular line or child line - use its own scanned qty
                total_scanned_qty = record.get_total_qty()

            record.on_hand_qty = on_hand_qty
            record.total_scanned_qty = total_scanned_qty
            record.forecast_qty = sum(product_quants.mapped('available_quantity'))
            record.unit_price = product.quantity_svl > 0 and product.value_svl / product.quantity_svl or 0.0

    @api.depends('total_scanned_qty', 'on_hand_qty')
    def _compute_difference_qty(self):
        for record in self:
            record.difference_qty = record.total_scanned_qty - record.on_hand_qty

    def get_total_qty(self):
        """
        Calculate the total scanned quantity across all adjustment line info.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        total_qty = 0
        product_uom = self.product_uom_id
        for line in self.adjustment_line_info_ids:
            total_qty += line.product_uom_id._compute_quantity(
                line.scanned_qty, product_uom, rounding_method='HALF-UP') if line.product_uom_id != product_uom else line.scanned_qty
        return total_qty

    def action_open_stock_adjustment_barcode_line_info(self):
        """
        Open the stock adjustment barcode line info action view.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        return self.inv_adjustment_id.open_action_view(
            action_xml_id='stock_adjustment_barcode.stock_adjustment_barcode_line_info_action',
            field_name='inv_adjustment_line_id', record_ids=self.ids)

    def action_show_details(self):
        """
        Open the stock adjustment barcode lot line action view.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        return self.inv_adjustment_id.open_action_view(
            action_xml_id='stock_adjustment_barcode.stock_adjustment_barcode_lot_line_action',
            field_name='inv_adjustment_line_id', record_ids=self.ids)

    def set_lot_on_adjustment_line_ids(self):
        """
        Set the lot details for the adjustment lines based on stock availability and quantity.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        product = self.product_id
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_scanned_qty = self.total_scanned_qty
        location = self.inv_adjustment_id.location_id
        lot_details_lst = [(2, line_details.id) for line_details in self.adjustment_line_lot_ids]

        quants = self.env['stock.quant']._gather(product, location)
        quant_found_in_location = True
        if not quants:
            ### Look for quant in the entire company in customer, internal or transit locations. Here current qty of quant will be zero
            lots = self.env['stock.lot'].search([
                ('product_id', '=', product.id),
                ('company_id', '=', self.company_id.id)
            ])
            quants = lots.quant_ids.filtered(lambda q: q.location_id.usage in ['customer', 'internal', 'transit'])
            quants = quants and quants[0] or False
            quant_found_in_location = False
            if not quants:
                raise ValidationError(_(
                    f"You cannot validate this stock operation because there are no quants available for the product "
                    f"'{product.display_name}'. "))

        if not quant_found_in_location:
            lot_details_lst.append((0, 0, {
                'lot_id': quants[0].lot_id.id,
                'new_qty': new_scanned_qty,
                'current_qty': 0,
            }))

        else:
            positive_quants = quants.filtered(lambda q: q.quantity > 0).sorted(lambda x: x.in_date)
            negative_quants = quants.filtered(lambda q: q.quantity < 0).sorted(lambda x: x.in_date)
            applied_quants = self.env['stock.quant']

            all_negative_quants = negative_quants and not positive_quants

            index = 1
            for quant in negative_quants:
                ### Mark all -ve quants 0
                ### Assign new_qty to first quant if all_negative_quants
                new_qty = new_scanned_qty if all_negative_quants and index == 1 else 0
                lot_details_lst.append((0, 0, {
                    'lot_id': quant.lot_id.id,
                    'new_qty': new_qty,
                    'current_qty': quant.quantity,
                }))
                applied_quants |= quant
                index += 1

            if positive_quants:
                difference = new_scanned_qty - sum(positive_quants.mapped('quantity'))
                if difference > 0:
                    ### Apply on the first
                    first_positive_quant = positive_quants[0]
                    lot_details_lst.append((0, 0, {
                        'lot_id': first_positive_quant.lot_id.id,
                        'new_qty': first_positive_quant.quantity + difference,
                        'current_qty': first_positive_quant.quantity,
                    }))
                    applied_quants |= first_positive_quant

                else:
                    ### Keep applying from the first until difference is 0
                    quant_index = 0
                    taken_quantity = abs(difference)
                    while (int(taken_quantity) > 0):
                        quant = positive_quants[quant_index]
                        lot_details_lst.append((0, 0, {
                            'lot_id': quant.lot_id.id,
                            'new_qty': max(0, quant.quantity - taken_quantity),
                            'current_qty': quant.quantity,
                        }))
                        taken_quantity -= float_round(quant.quantity, precision_digits=precision)
                        applied_quants |= quant
                        quant_index += 1

            pending_quants = quants - applied_quants
            for quant in pending_quants:
                lot_details_lst.append((0, 0, {
                    'lot_id': quant.lot_id.id,
                    'new_qty': quant.quantity,
                    'current_qty': quant.quantity,
                }))

            # for index, quant in enumerate(quants.sorted(key=lambda q: q.quantity), start=1):
            #     lot_details_lst.append((0, 0, {
            #         'lot_id': quant.lot_id.id,
            #         'new_qty': difference_qty if index == 1 else 0,
            #         'current_qty': quant_found_in_location and quant.quantity or 0.0,
            #     }))

        self.write({'adjustment_line_lot_ids': lot_details_lst})

    def set_lot_on_adjustment_line_ids_difference(self, difference, quants):
        """
        Set the lot details for the adjustment lines based on stock availability and quantity.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        product = self.product_id
        new_scanned_qty = self.total_scanned_qty
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        lot_details_lst = [(2, line_details.id) for line_details in self.adjustment_line_lot_ids]
        quant_found_in_location = True
        if not quants:
            ### Look for quant in the entire company in customer, internal or transit locations. Here current qty of quant will be zero
            lots = self.env['stock.lot'].search([
                ('product_id', '=', product.id),
                ('company_id', '=', self.company_id.id)
            ])
            quants = lots.quant_ids.filtered(lambda q: q.location_id.usage in ['customer', 'internal', 'transit'])
            quants = quants and quants[0] or False
            quant_found_in_location = False
            if not quants:
                return False

        if not quant_found_in_location:
            lot_details_lst.append((0, 0, {
                'lot_id': quants[0].lot_id.id,
                'new_qty': new_scanned_qty,
                'current_qty': 0,
            }))

        else:
            positive_quants = quants.filtered(lambda q: q.quantity > 0).sorted(lambda x: x.in_date)
            negative_quants = quants.filtered(lambda q: q.quantity < 0).sorted(lambda x: x.in_date)
            applied_quants = self.env['stock.quant']

            all_negative_quants = negative_quants and not positive_quants

            index = 1
            for quant in negative_quants:
                ### Mark all -ve quants 0
                ### Assign new_qty to first quant if all_negative_quants
                new_qty = new_scanned_qty if all_negative_quants and index == 1 else 0
                lot_details_lst.append((0, 0, {
                    'lot_id': quant.lot_id.id,
                    'new_qty': new_qty,
                    'current_qty': quant.quantity,
                }))
                applied_quants |= quant
                index += 1

            if positive_quants:
                # difference = new_scanned_qty - sum(positive_quants.mapped('quantity'))
                if difference > 0:
                    ### Apply on the first
                    first_positive_quant = positive_quants[0]
                    lot_details_lst.append((0, 0, {
                        'lot_id': first_positive_quant.lot_id.id,
                        'new_qty': first_positive_quant.quantity + difference,
                        'current_qty': first_positive_quant.quantity,
                    }))
                    applied_quants |= first_positive_quant

                else:
                    ### Keep applying from the first until difference is 0
                    quant_index = 0
                    taken_quantity = abs(difference)
                    while (int(taken_quantity) > 0):
                        quant = positive_quants[quant_index]
                        lot_details_lst.append((0, 0, {
                            'lot_id': quant.lot_id.id,
                            'new_qty': max(0, quant.quantity - taken_quantity),
                            'current_qty': quant.quantity,
                        }))
                        taken_quantity -= float_round(quant.quantity, precision_digits=precision)
                        applied_quants |= quant
                        quant_index += 1

            pending_quants = quants - applied_quants
            for quant in pending_quants:
                lot_details_lst.append((0, 0, {
                    'lot_id': quant.lot_id.id,
                    'new_qty': quant.quantity,
                    'current_qty': quant.quantity,
                }))

            # for index, quant in enumerate(quants.sorted(key=lambda q: q.quantity), start=1):
            #     lot_details_lst.append((0, 0, {
            #         'lot_id': quant.lot_id.id,
            #         'new_qty': difference_qty if index == 1 else 0,
            #         'current_qty': quant_found_in_location and quant.quantity or 0.0,
            #     }))

        self.write({'adjustment_line_lot_ids': lot_details_lst})
        return True

    # def set_lot_on_adjustment_line_ids_old(self):
    #     """
    #     Set the lot details for the adjustment lines based on stock availability and quantity.
    #     TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
    #     """
    #     product = self.product_id
    #     adjusted_qty = self.difference_qty
    #     stock_quant = self.env['stock.quant']
    #     location = self.inv_adjustment_id.location_id
    #     precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #     lot_details_lst = [(2, line_details.id) for line_details in self.adjustment_line_lot_ids]
    #     if self.lot_id:
    #         if adjusted_qty < 0:
    #             quants = stock_quant._gather(product, location, lot_id=self.lot_id)
    #             available_qty = sum(quants.mapped('quantity'))
    #             if float_compare(available_qty, abs(adjusted_qty), precision_digits=precision) < 0:
    #                 raise ValidationError(_(
    #                     f"You cannot validate this stock operation because the stock level of the product "
    #                     f"'{product.display_name}' would become negative ({available_qty}) on the stock location "
    #                     f"'{location.complete_name}' and negative stock is not allowed for this product and/or location."))

    #         lot_details_lst.append((0, 0, {'lot_id': self.lot_id.id, 'difference_qty': adjusted_qty}))
    #     else:
    #         quants = stock_quant._gather(product, location)
    #         if not quants:
    #             raise ValidationError(_(
    #                 f"You cannot validate this stock operation because there are no lots available for the product "
    #                 f"'{product.display_name}' on the stock location '{location.complete_name}'. "))

    #         if adjusted_qty > 0:
    #             lot_details_lst.append((0, 0, {'lot_id': quants[0].lot_id.id, 'difference_qty': adjusted_qty}))
    #         else:
    #             adjusted_qty = abs(adjusted_qty)
    #             available_qty = sum(quants.mapped('quantity'))
    #             if float_compare(available_qty, adjusted_qty, precision_digits=precision) < 0:
    #                 raise ValidationError(_(
    #                     f"You cannot validate this stock operation because the stock level of the product "
    #                     f"'{product.display_name}' would become negative ({available_qty}) on the stock location "
    #                     f"'{location.complete_name}' and negative stock is not allowed for this product and/or location."))
    #             taken_quantity = adjusted_qty
    #             for quant in quants:
    #                 if taken_quantity <= 0:
    #                     break

    #                 difference_qty = min(taken_quantity, quant.quantity)
    #                 lot_details_lst.append((0, 0, {'lot_id': quant.lot_id.id, 'difference_qty': -difference_qty}))
    #                 taken_quantity -= difference_qty

    #     self.write({'adjustment_line_lot_ids': lot_details_lst})

    def unlink(self):
        """
        Unlink the stock adjustment barcode line after checking state restrictions.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        approval_user = self.user_has_groups('stock_adjustment_barcode.approve_stock_adjustment_barcode_group')

        if approval_user and self.inv_adjustment_id.filtered(lambda l: l.state not in ['draft', 'to_approve']):
            raise ValidationError(_("You can delete lines only in 'Draft' / 'To Approve' state."))

        elif not approval_user and self.inv_adjustment_id.filtered(lambda l: l.state != 'draft'):
            raise ValidationError(_("You can delete lines only in 'Draft' state."))

        return super().unlink()
