# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    inv_adjustment_line_id = fields.Many2one('stock.adjustment.barcode.line')
