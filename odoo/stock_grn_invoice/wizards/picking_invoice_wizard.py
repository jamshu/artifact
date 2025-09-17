from collections import defaultdict
from odoo import models, fields, _
from odoo.tools import groupby
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError, ValidationError


class PickingInvoiceWizard(models.TransientModel):
    _name = 'picking.invoice.wizard'
    _description = 'Picking Invoice Wizard'

    order_ids = fields.Many2many('purchase.order', string='Purchase Order')
    stock_picking_ids = fields.Many2many('stock.picking', string='Stock Pickings', domain="[('purchase_id', 'in', order_ids), ('grn_invoice_ids', '=', False), ('state', '=', 'done')]")

    def create_account_move(self):
        """Create the invoice associated to the PO."""
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        if not self.stock_picking_ids:
            raise ValidationError(_('Please select a shipment before creating the bill'))

        # 1) Calculate net quantities for all products
        product_dict = defaultdict(lambda: 0)
        purchase_line_list = []
        
        for picking_id in self.stock_picking_ids:
            for move_line in picking_id.move_line_ids:
                purchase_line = move_line.move_id.purchase_line_id
                if not purchase_line:
                    continue
                    
                qty_in_po_uom = move_line.product_uom_id._compute_quantity(
                    move_line.qty_done, purchase_line.product_uom
                )
                
                # Receipts: from supplier/external to internal location (positive quantity)
                if move_line.location_dest_usage == 'internal' and move_line.location_usage != 'internal':
                    product_dict[purchase_line.id] += qty_in_po_uom
                # Returns: from internal to supplier/external location (negative quantity)
                elif move_line.location_usage == 'internal' and move_line.location_dest_usage != 'internal':
                    product_dict[purchase_line.id] -= qty_in_po_uom
                    
                if purchase_line.id not in purchase_line_list:
                    purchase_line_list.append(purchase_line.id)

        # 2) Check if all quantities are positive, negative, or mixed
        has_positive = False
        has_negative = False
        has_zero = False
        
        for purchase_line_id, net_qty in product_dict.items():
            if float_is_zero(net_qty, precision_digits=precision):
                has_zero = True
            elif net_qty > 0:
                has_positive = True
            else:  # net_qty < 0
                has_negative = True
        
        # 3) Validate the scenario and determine document type
        if has_positive and has_negative:
            raise UserError(
                _("Cannot create a bill with mixed positive and negative quantities.\n"
                  "Some products have net positive quantities (more receipts than returns) "
                  "while others have net negative quantities (more returns than receipts).\n\n"
                  "Please either:\n"
                  "- Select only receipts to create a vendor bill\n"
                  "- Select only returns to create a credit note\n"
                  "- Ensure all products have the same sign for net quantities")
            )
        
        # Determine the move type based on net quantities
        move_type = 'in_invoice'  # Default: vendor bill
        if has_negative and not has_positive:
            move_type = 'in_refund'  # All negative: credit note
        
        # 4) Prepare invoice values
        invoice_vals_list = []
        sequence = 10
        
        for order in self.order_ids.filtered(lambda order: order.bill_creation_source in ['receipts','initial']):
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Override move type
            invoice_vals['move_type'] = move_type
            
            # Invoice line values (keep only necessary sections)
            for line in order.order_line.filtered(lambda line: line.id in purchase_line_list):
                move_line_qty = product_dict.get(line.id, 0.0)
                
                # Skip lines with zero quantity
                if float_is_zero(move_line_qty, precision_digits=precision):
                    continue
                    
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                    
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        line_vals = pending_section._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                        pending_section = None
                    
                    line_vals = line._prepare_account_move_line()
                    # Use absolute value for credit notes to ensure positive quantities in the document
                    if move_type == 'in_refund':
                        line_vals.update({'sequence': sequence, 'quantity': abs(move_line_qty)})
                    else:
                        line_vals.update({'sequence': sequence, 'quantity': move_line_qty})
                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1
            
            if invoice_vals.get('invoice_line_ids'):
                invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id, invoice_origin) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 5) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type=move_type)
        for vals in invoice_vals_list:
            if not vals.get('invoice_line_ids', False):
                continue
            vals["grn_picking_ids"] = [(6, 0, self.stock_picking_ids.ids)]
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # Note: We don't need to auto-switch to refund anymore since we're explicitly setting the type
        # based on net quantities analysis
        
        self.order_ids.write({'bill_creation_source': 'receipts'})
        return self.order_ids.action_view_invoice(moves)
