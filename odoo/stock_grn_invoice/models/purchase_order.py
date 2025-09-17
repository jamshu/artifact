from odoo.exceptions import UserError
from odoo import api, models, fields, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    bill_creation_source = fields.Selection([('initial', 'Initial'), ('order', 'Order'), ('receipts', 'Receipts')], 'Bill Creation Source', default='initial')

    # @api.onchange('invoice_ids')
    # def _onchange_invoice_ids(self):
    #     This is the idle function to update bill_creation_source. But this is not getting called
    #     if not self.invoice_count:
    #         self.bill_creation_source = 'initial'

    @api.depends('order_line.invoice_lines.move_id')
    def _compute_invoice(self):
        ### This will update bill_creation_source when the invoices are deleted
        super()._compute_invoice()
        for order in self:
            if not order.invoice_count:
                order.bill_creation_source = 'initial'

    def action_open_create_bill_from_receipts_from_window(self):
        for order in self:
            if order.state not in ['purchase', 'done'] or order.order_line == []:
                raise UserError(_("Only Confirm and Done PO's bill can be created. This PO '%s' not in Confirm or Done state.", order.name))
            if order.invoice_status in ['no', 'invoiced']:
                raise UserError(_("This PO's '%s' bill has been created.", order.name))
        return self.action_open_create_bill_from_receipts()

    def action_open_create_bill_from_receipts(self):
        return {
            'name': 'Create Bill From Receipts',
            'type': 'ir.actions.act_window',
            'res_model': 'picking.invoice.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_order_ids': self.ids}
        }

    def action_create_invoice(self):
        self_order_source = self.filtered(lambda o: o.bill_creation_source !=  'receipts')
        result = super(PurchaseOrder, self_order_source).action_create_invoice()
        self.write({'bill_creation_source': 'order'})
        return result