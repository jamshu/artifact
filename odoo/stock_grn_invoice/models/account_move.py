from odoo.exceptions import UserError
from odoo import fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    grn_picking_ids = fields.Many2many('stock.picking', 'account_move_grn_picking_rel','move_id','picking_id', string='GRN Pickings')

    def _update_po_bill_data(self):
        self.grn_picking_ids.write({"grn_invoice_ids": [(5, 0, 0)]})
        vendor_bill_non_cancel = self.invoice_line_ids.purchase_line_id.order_id.invoice_ids.filtered(
            lambda i: i.state != 'cancel')
        if not vendor_bill_non_cancel:
            self.invoice_line_ids.purchase_line_id.order_id.bill_creation_source = 'initial'

    def unlink(self):
        ### We cannot call _update_po_bill_data() from here bcoz afer super() the bill is deleted and before the invoice count is > 0
        for record in self:
            record.grn_picking_ids.write({"grn_invoice_ids": [(5, 0, 0)]})
        return super(AccountMove, self).unlink()

    def button_cancel(self):
        result = super(AccountMove, self).button_cancel()
        for record in self:
            record._update_po_bill_data()
        return result

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def unlink(self):
        for line in self:
            if not self.env.context.get('dynamic_unlink', False) and line.purchase_line_id.order_id.bill_creation_source == 'receipts':
                raise UserError(_("You can't delete a line while you had created bill from receipt."))
        return super(AccountMoveLine, self).unlink()
