# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockAdjustmentBarcodeLotLine(models.Model):
    _name = 'stock.adjustment.barcode.lot.line'
    _description = 'Stock Adjustment Barcode Lot Line'

    inv_adjustment_line_id = fields.Many2one(
        comodel_name='stock.adjustment.barcode.line',
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        related='inv_adjustment_line_id.product_id'
    )

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id)]"
    )

    current_qty = fields.Float()
    new_qty = fields.Float()

    difference_qty = fields.Float(
        compute='_compute_lot_difference_qty',
        store=True
    )

    @api.depends('current_qty', 'new_qty')
    def _compute_lot_difference_qty(self):
        for record in self:
            record.difference_qty = record.new_qty - record.current_qty
