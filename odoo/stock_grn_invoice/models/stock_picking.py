from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    grn_invoice_ids = fields.Many2many('account.move', 'account_move_grn_picking_rel','picking_id','move_id', string='GRN Invoices')


    