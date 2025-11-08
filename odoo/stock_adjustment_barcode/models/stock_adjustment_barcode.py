# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.tools.misc import groupby
from lxml import etree
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class StockAdjustmentBarcode(models.Model):
    _name = 'stock.adjustment.barcode'
    _description = 'Stock Adjustment Barcode'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'barcodes.barcode_events_mixin']
    _order = 'inventory_date desc'

    name = fields.Char(
        string='Sequence Number',
        default=lambda self: _('New'),
        required=True,
        copy=False,
        readonly=True
    )

    is_recompute = fields.Boolean(
        default=False,
        copy=False
    )

    force_accounting_date = fields.Date(
        tracking=True,
        copy=False
    )

    inventory_date = fields.Datetime(
        default=lambda self: fields.Datetime.now(),
        tracking=True,
        copy=False
    )

    posted_date = fields.Datetime(
        tracking=True,
        copy=False
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], default='draft', tracking=True)

    location_id = fields.Many2one(
        comodel_name='stock.location',
        domain="[('usage', '=', 'internal')]",
        tracking=True,
        check_company=True,
    )

    approved_by = fields.Many2one(
        comodel_name='res.users',
        copy=False
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    currency_id = fields.Many2one('res.currency', 'Currency', related='company_id.currency_id', readonly=True, required=True)

    disallowed_products_json = fields.Json(
        string='Disallowed Products',
        help='JSON field to track products that should not be scanned directly (like Arjoon Mamool Assorted 400 gms 3 in 1)',
        default=list
    )

    inv_adjustment_line_ids = fields.One2many(
        comodel_name='stock.adjustment.barcode.line',
        inverse_name='inv_adjustment_id',
        copy=False
    )

    inv_adjustment_line_info_ids = fields.One2many(
        comodel_name='stock.adjustment.barcode.line.info',
        inverse_name='inv_adjustment_id',
        copy=False,
        domain=lambda self: [('create_uid', '=', self.env.user.id)]
    )

    def on_barcode_scanned(self, barcode):
        """
        Handles barcode scan and updates adjustment line based on scanned product or lot.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_("You can only scan lines in the 'draft' state."))

        lot = self.env['stock.lot']
        inv_adjustment_id = self.id or self._origin.id

        product = self.env['product.product'].search([('barcode', '=', barcode)])
        # if not product:
        #     lot = self.env['stock.lot'].search([('name', '=', barcode)])
        #     product = lot.product_id
        if not product:
            # msg = f"You scanned the wrong barcode: {barcode}. The product or Lot/Serial Number is not available in the system."
            raise UserError(_(f"The product is not available in the system with this barcode {barcode}."))

        # Auto-initialize disallowed products if not already done
        # if not self.disallowed_products_json:
        #     self._auto_initialize_disallowed_products()
        #
        # Check if the product is in the disallowed products list
        disallowed_products = self.disallowed_products_json or []
        if product.id in disallowed_products:
            raise UserError(_(f"Product '{product.name}' is not allowed to be scanned directly. It should appear as a parent product when scanning its child products."))

        current_user = self.env.user
        last_scanned_line = self.inv_adjustment_line_info_ids and self.inv_adjustment_line_info_ids[-1] or self.inv_adjustment_line_info_ids

        # if last_scanned_line.product_id == product and last_scanned_line.lot_id == lot and last_scanned_line.scanned_user_id == current_user:
        if last_scanned_line.product_id == product and last_scanned_line.scanned_user_id == current_user:
            last_scanned_line.scanned_qty += 1
        else:
            self.inv_adjustment_line_info_ids += self.env['stock.adjustment.barcode.line.info'].new({
                'lot_id': lot.id,
                'product_id': product.id,
                'scanned_user_id': current_user.id,
                'inv_adjustment_id': inv_adjustment_id,
            })

    def action_confirm(self):
        """
        Confirms the stock adjustment and prepares lines for approval.
        Also handles BOM transfer consolidation logic.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        if not self.env.context.get('avoid_zero_lines', False) and not self.inv_adjustment_line_ids:
            raise ValidationError(_("No Lines are created yet."))

        # Handle BOM transfer consolidation before creating zero stock lines
        self._handle_bom_transfer_consolidation()

        self.prepare_and_create_zero_stock_lines()

        for line in self.inv_adjustment_line_ids:
            line.set_lot_on_adjustment_line_ids()

        self.write({'state': 'to_approve'})

    def _handle_bom_transfer_consolidation(self):
        """
        Handle BOM transfer consolidation logic.
        For products that have BOM transfer type, consolidate their scanned quantities
        to their parent products and create parent lines. Keep child lines visible for reference.
        Also copies child scanned line info records to parent for full audit trail.
        """
        # Get all lines that need BOM transfer consolidation
        parent_products = {}
        
        for line in self.inv_adjustment_line_ids:
            parent_product = line._find_parent_product_from_bom_transfer()
            if parent_product:
                if parent_product not in parent_products:
                    parent_products[parent_product] = {'child_lines': [], 'total_qty': 0}
                parent_products[parent_product]['child_lines'].append(line)
                parent_products[parent_product]['total_qty'] += line.total_scanned_qty
        
        # Create/update parent lines and mark child lines
        for parent_product, data in parent_products.items():
            # Check if parent line already exists
            existing_parent_line = self.inv_adjustment_line_ids.filtered(
                lambda l: l.product_id == parent_product and not l.parent_product_id
            )
            
            if not existing_parent_line:
                # Create parent line with explicit low sequence
                parent_line_vals = {
                    'product_id': parent_product.id,
                    'inv_adjustment_id': self.id,
                    'parent_product_id': False,  # This is the parent line
                    'display_sequence': 1000 + (parent_product.id * 10),  # Set explicit sequence
                }
                parent_line = self.env['stock.adjustment.barcode.line'].create(parent_line_vals)
                
                # Add to disallowed products so it can't be scanned directly
                disallowed_products = self.disallowed_products_json or []
                if parent_product.id not in disallowed_products:
                    disallowed_products.append(parent_product.id)
                    self.disallowed_products_json = disallowed_products
            else:
                parent_line = existing_parent_line[0]
                # Update sequence for existing parent line
                parent_line.write({
                    'display_sequence': 1000 + (parent_product.id * 10)
                })
            
            # Convert child_lines list to recordset
            child_lines_recordset = self.env['stock.adjustment.barcode.line'].browse(
                [line.id for line in data['child_lines']]
            )
            
            # Copy child scanned line info records to parent line
            # This allows viewing all related scans from the parent
            self._copy_child_line_info_to_parent(parent_line, child_lines_recordset)
            
            # Calculate child sequences and mark with parent reference
            for idx, child_line in enumerate(child_lines_recordset, start=1):
                child_line.write({
                    'parent_product_id': parent_product.id,
                    'display_sequence': 1000 + (parent_product.id * 10) + idx,  # Parent seq + offset
                })
            
            # Keep child line info with children for tracking
            # Parent now has copies of all child line info records for consolidated view
        
        # Recalculate computed fields for all lines after consolidation
        self.inv_adjustment_line_ids._compute_is_parent_line()
        self.inv_adjustment_line_ids._compute_is_child_line()
        self.inv_adjustment_line_ids._compute_display_sequence()

    def _copy_child_line_info_to_parent(self, parent_line, child_lines):
        """
        Copy child scanned line info records to parent line.
        This creates duplicate info records on the parent so all related scans
        can be viewed from the parent line itself.
        
        Args:
            parent_line: The parent adjustment line (stock.adjustment.barcode.line)
            child_lines: Recordset of child adjustment lines
        """
        line_info_obj = self.env['stock.adjustment.barcode.line.info']
        
        # Debug logging
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Copying child line info to parent line ID: {parent_line.id}, Product: {parent_line.product_id.name}")
        
        # Collect all child line info records
        all_child_line_info = self.env['stock.adjustment.barcode.line.info']
        for child_line in child_lines:
            all_child_line_info |= child_line.adjustment_line_info_ids
            _logger.info(f"  - Child line ID: {child_line.id}, Product: {child_line.product_id.name}, Info count: {len(child_line.adjustment_line_info_ids)}")
        
        # Create copies of each child line info record for the parent
        for child_info in all_child_line_info:
            # Check if this exact info record already exists on parent
            # (to avoid duplicates if consolidation runs multiple times)
            existing_parent_info = parent_line.adjustment_line_info_ids.filtered(
                lambda i: i.product_id == child_info.product_id and 
                         i.scanned_qty == child_info.scanned_qty and 
                         i.scanned_user_id == child_info.scanned_user_id and
                         i.lot_id == child_info.lot_id
            )
            
            if not existing_parent_info:
                # Create a copy of the child info record for the parent
                new_info_vals = {
                    'product_id': child_info.product_id.id,
                    'lot_id': child_info.lot_id.id if child_info.lot_id else False,
                    'product_uom_id': child_info.product_uom_id.id,
                    'scanned_qty': child_info.scanned_qty,
                    'scanned_user_id': child_info.scanned_user_id.id,
                    'inv_adjustment_id': self.id,
                    'inv_adjustment_line_id': parent_line.id,  # Link to parent line
                }
                _logger.info(f"  Creating line info copy with inv_adjustment_line_id={parent_line.id} for product {child_info.product_id.name}")
                new_info = line_info_obj.create(new_info_vals)
                _logger.info(f"  Created line info ID {new_info.id} linked to line ID {new_info.inv_adjustment_line_id.id}")

    def action_set_zero_values(self):
        self.with_context(avoid_zero_lines=True).action_confirm()

    def prepare_and_create_zero_stock_lines(self):
        """
        Prepares and creates zero stock lines for products not yet scanned.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        quants = self.get_quant_ids()
        adjustment_line_info_lst = list()

        for quant in quants:
            adjustment_line_info_lst.append({
                'scanned_qty': 0,
                'inv_adjustment_id': self.id,
                'product_id': quant.product_id.id,
            })

        if adjustment_line_info_lst:
            self.env['stock.adjustment.barcode.line.info'].with_user(SUPERUSER_ID).create(adjustment_line_info_lst)

    def get_quant_ids(self):
        if self.env.context.get('avoid_zero_lines'):
            cursor = self.env.cr
            cursor.execute(f"""
                SELECT
                    array_agg(sq.id) AS ids
                FROM
                    stock_quant AS sq
                        INNER JOIN product_product AS pp
                            ON sq.product_id = pp.id AND pp.active = TRUE
                WHERE
                    sq.location_id = {self.location_id.id}
                    AND sq.company_id = {self.company_id.id}
                GROUP BY
                    sq.product_id
                HAVING
                    SUM(sq.quantity) = 0
            """)
            result = cursor.dictfetchall()
            quant_ids = [ids for sublist in result for ids in sublist['ids']] if result else list()
            return self.env['stock.quant'].sudo().browse(quant_ids)

        return self.env['stock.quant'].sudo().search([
            ('product_id.active', '=', True),
            ('company_id', '=', self.company_id.id),
            ('location_id', '=', self.location_id.id),
            ('product_id', 'not in', self.inv_adjustment_line_ids.product_id.ids)])

    def action_approved(self):
        """
        Approves the stock adjustment.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        if not self.inv_adjustment_line_ids:
            raise ValidationError(_("There are no lines for approval"))
        self.write({'state': 'approved', 'approved_by': self.env.user.id})

    def action_done(self):
        """
        Completes the stock adjustment by creating stock moves.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        if not self.inv_adjustment_line_ids:
            raise ValidationError(_("There is no Adjustment Lines."))

        self.action_recompute_lots()
        error_lines = self.inv_adjustment_line_ids.filtered(lambda l: l.is_editable)

        if error_lines:
            product_names = error_lines.product_id.mapped('name')
            self.message_post(body=f"Please resolve the stock mismatch for the following products <br/> {', '.join(product_names)}")
        else:
            self.create_stock_move()
            self.write({'state': 'done'})

    def action_refresh_stock(self):
        """
        Refreshes the stock information for the adjustment lines.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        self.inv_adjustment_line_ids._compute_product_qty()

    def action_recompute_lots(self):
        quant_obj = self.env['stock.quant']

        for line in self.inv_adjustment_line_ids:
            lot_qty = sum(line.adjustment_line_lot_ids.mapped('current_qty'))
            vals = {'on_hand_qty': lot_qty}
            difference = line.total_scanned_qty - lot_qty
            quants = quant_obj._gather(line.product_id, line.inv_adjustment_id.location_id)
            quant_quantity = sum(quants.mapped('quantity'))
            if difference < 0 and (quant_quantity < 0 or abs(difference) > abs(quant_quantity)):
                vals.update({'is_editable': True})
            else:
                line.set_lot_on_adjustment_line_ids_difference(difference, quants)
                vals.update({'is_editable': False})

            line.write(vals)

        if not self.is_recompute:
            self.is_recompute = True

    def action_cancel(self):
        """
        Cancels the stock adjustment if it's in a cancellable state.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        if self.filtered(lambda s: s.state in ('cancel', 'done')):
            raise ValidationError(_("You are not allowed to cancel this record."))
        self._cleanup_bom_transfer_consolidation()
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        """
        Resets the stock adjustment to 'draft' if it's in 'cancel' state.
        Also cleans up BOM transfer consolidation data.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        if self.filtered(lambda s: s.state != 'cancel'):
            raise ValidationError(_("Only cancelled records can be reset to draft."))
        
        # Clean up consolidation data when resetting to draft

        
        self.write({'state': 'draft'})

    def _cleanup_bom_transfer_consolidation(self):
        """
        Clean up BOM transfer consolidation data when resetting to draft.
        Remove parent product references, copied line info records, and clean up disallowed products list.
        """
        # Find parent lines that were created during consolidation
        parent_lines = self.inv_adjustment_line_ids.filtered(lambda l: l.is_parent_line)
        
        # Remove copied line info records from parent lines
        # Keep only line info records that belong to child lines
        for parent_line in parent_lines:
            # Get all child lines for this parent
            child_lines = self.inv_adjustment_line_ids.filtered(
                lambda l: l.parent_product_id == parent_line.product_id
            )
            
            # Collect all child line info IDs
            child_line_info_ids = set()
            for child_line in child_lines:
                child_line_info_ids.update(child_line.adjustment_line_info_ids.ids)
            
            # Remove parent line info records that are copies from children
            # (these are the records that were copied to parent during consolidation)
            parent_info_to_remove = parent_line.adjustment_line_info_ids.filtered(
                lambda info: info.product_id != parent_line.product_id
            )
            parent_info_to_remove.unlink()
        
        # Reset parent_product_id for all child lines
        child_lines = self.inv_adjustment_line_ids.filtered(lambda l: l.parent_product_id)
        child_lines.write({'parent_product_id': False})
        
        # Remove parent lines that were auto-created during consolidation
        # (parent lines that have no original line info or were created by consolidation)
        parent_lines_to_remove = self.inv_adjustment_line_ids.filtered(
            lambda l: l.is_parent_line
        )
        
        # Check if parent line was manually created or auto-created
        # Auto-created parent lines typically have only copied info records
        for parent_line in parent_lines_to_remove:
            # If parent line has no line info after cleanup, it was auto-created
            if not parent_line.adjustment_line_info_ids:
                parent_line.unlink()
        
        # Clear disallowed products list
        self.disallowed_products_json = []

    def action_initialize_disallowed_products(self):
        """
        Initialize disallowed products list with parent products from BOM transfers.
        Find all products that are parent products in BOM transfer type.
        """
        # Find all BOMs of type 'transfer' that are applicable to this warehouse/location
        warehouse = self.location_id.warehouse_id or self.location_id.get_warehouse()
        
        domain = [('type', '=', 'transfer')]
        if warehouse:
            domain = ['|', ('warehouse_ids', '=', False), ('warehouse_ids', 'in', [warehouse.id])] + domain
        
        transfer_boms = self.env['mrp.bom'].search(domain)
        
        # Get all parent products from these BOMs (products that have components in BOM lines)
        parent_products = set()
        for bom in transfer_boms:
            if bom.bom_line_ids:
                # Get the parent product from bom_line_ids (first component is the parent)
                parent_product = bom.bom_line_ids[0].product_id
                parent_products.add(parent_product.id)
        
        if parent_products:
            self.disallowed_products_json = list(parent_products)
            parent_product_names = self.env['product.product'].browse(list(parent_products)).mapped('name')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _(f'Added {len(parent_products)} parent product(s) to disallowed list: {" ,".join(parent_product_names[:3])}{", ..." if len(parent_product_names) > 3 else ""}'),
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Info'),
                    'message': _('No BOM transfer parent products found to add to disallowed list'),
                    'sticky': False,
                }
            }

    def _auto_initialize_disallowed_products(self):
        """
        Automatically initialize disallowed products list with parent products from BOM transfers.
        This is called during barcode scanning if the list is empty.
        """
        # Find all BOMs of type 'transfer' that are applicable to this warehouse/location
        warehouse = self.location_id.warehouse_id or self.location_id.get_warehouse()
        
        domain = [('type', '=', 'transfer')]
        if warehouse:
            domain = ['|', ('warehouse_ids', '=', False), ('warehouse_ids', 'in', [warehouse.id])] + domain
        
        transfer_boms = self.env['mrp.bom'].search(domain)
        
        # Get all parent products from these BOMs (products that have components in BOM lines)
        parent_products = set()
        for bom in transfer_boms:
            if bom.bom_line_ids:
                # Get the parent product from bom_line_ids (first component is the parent)
                parent_product = bom.bom_line_ids[0].product_id
                parent_products.add(parent_product.id)
        
        if parent_products:
            self.disallowed_products_json = list(parent_products)

    def create_stock_move(self):
        """
        Creates stock moves for each inventory adjustment line in 'approved' state.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        stock_move_lst = list()
        today = fields.Date.today()
        stock_quant = self.env['stock.quant']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for record in self.filtered(lambda s: s.state == 'approved'):
            company = record.company_id
            # Only process parent lines and lines without parent (ignore child lines)
            lines_to_process = record.inv_adjustment_line_ids.filtered(
                lambda l: not l.is_child_line
            )
            for line in lines_to_process:
                inventory_location = line.product_id.with_company(company).property_stock_inventory

                for lot_line in line.adjustment_line_lot_ids.filtered(lambda l: l.difference_qty != 0):

                    if lot_line.difference_qty < 0:
                        ### Check if the quant of the lot will not become -ve
                        quants = stock_quant.search([
                            ('lot_id', '=', lot_line.lot_id.id),
                            ('product_id', '=', lot_line.product_id.id),
                            ('location_id', '=', record.location_id.id)])
                        available_qty = sum(quants.mapped('quantity'))  ### It will consider qty on hand and not available_qty.

                        if float_compare(available_qty, abs(lot_line.difference_qty), precision_digits=precision) < 0:
                            raise ValidationError(
                                _(
                                    "You cannot validate this stock operation because the "
                                    "stock level of the product '{name}' would "
                                    "become negative "
                                    "({q_quantity}) on the stock location '{complete_name}' "
                                    "and negative stock is "
                                    "not allowed for this product and/or location."
                                ).format(
                                    name=lot_line.product_id.display_name,
                                    q_quantity=available_qty,
                                    complete_name=record.location_id.complete_name,
                                )
                            )
                        location_id = record.location_id.id
                        location_dest_id = inventory_location.id
                    else:
                        location_id = inventory_location.id
                        location_dest_id = record.location_id.id

                    move_vals = {
                        'company_id': company.id,
                        'inv_adjustment_line_id': line.id,
                        'is_inventory': True,
                        'location_dest_id': location_dest_id,
                        'location_id': location_id,
                        # 'move_line_ids': list(),
                        'origin': record.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom_id.id,
                        'product_uom_qty': abs(lot_line.difference_qty),
                        'state': 'confirmed',
                        'name': f"{record.name}-[{line.product_id.default_code}]-{line.product_id.name}",
                        'move_line_ids': [(0, 0, {
                            'company_id': company.id,
                            'location_dest_id': location_dest_id,
                            'location_id': location_id,
                            'lot_id': lot_line.lot_id.id,
                            'product_id': lot_line.product_id.id,
                            'product_uom_id': line.product_uom_id.id,
                            'qty_done': abs(lot_line.difference_qty)
                        })]
                    }

                    # for lot_line in line.adjustment_line_lot_ids:
                    #     move_vals['move_line_ids'].append((0, 0, {
                    #         'company_id': company.id,
                    #         'location_dest_id': location_dest_id,
                    #         'location_id': location_id,
                    #         'lot_id': lot_line.lot_id.id,
                    #         'product_id': lot_line.product_id.id,
                    #         'product_uom_id': line.product_uom_id.id,
                    #         'qty_done': abs(lot_line.difference_qty)
                    #     }))

                    stock_move_lst.append(move_vals)

        if not stock_move_lst:
            raise UserError(_("Something is wrong !!! Stock moves not created."))

        stock_moves = self.env['stock.move'].sudo().create(stock_move_lst)
        stock_moves.with_context(ignore_transfer_bom=True)._action_done()
        self.write({'posted_date': today})
        self.location_id.write({'last_inventory_date': today})

    @api.model_create_multi
    def create(self, vals_list):
        """
        Creates a new stock adjustment record with a unique sequence.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        ir_sequence_obj = self.env['ir.sequence']
        for vals in vals_list:
            if self.search([('location_id', '=', vals['location_id']), ('state', 'not in', ('done', 'cancel'))]):
                raise ValidationError(_("You can only have one active adjustment for a location!"))
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = ir_sequence_obj.next_by_code('inventory.adjustment.barcode.sequence')
        return super().create(vals_list)

    def action_view_stock_move(self):
        """
        Opens the related stock move records.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        return self.open_action_view(action_xml_id='stock.stock_move_action', field_name='id',
                                     record_ids=self.inv_adjustment_line_ids.stock_move_ids.ids)

    def action_view_account_move(self):
        """
        Opens the related account move records.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        return self.open_action_view(action_xml_id='account.action_move_journal_line', field_name='id',
                                     record_ids=self.inv_adjustment_line_ids.stock_move_ids.account_move_ids.ids)

    def action_view_stock_valuation_layers(self):
        """
        Opens the related stock valuation layers.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        return self.open_action_view(action_xml_id='stock_account.stock_valuation_layer_action',
                                     field_name='stock_move_id',
                                     record_ids=self.inv_adjustment_line_ids.stock_move_ids.ids)

    def action_open_scan_line(self):
        """
        Opens the scan form view for the stock adjustment record.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        self.ensure_one()
        self._auto_initialize_disallowed_products()
        form_view = self.env.ref('stock_adjustment_barcode.stock_adjustment_barcode_scan_form_view')
        return {
            'target': 'current',
            'name': self.name,
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': form_view.id,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.adjustment.barcode',
        }

    def open_action_view(self, action_xml_id, field_name, record_ids):
        """
        Opens an action view with the specified record IDs.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        self.ensure_one()
        action = self.env.ref(action_xml_id).sudo().read()[0]
        action['domain'] = [(field_name, 'in', record_ids)]
        return action
