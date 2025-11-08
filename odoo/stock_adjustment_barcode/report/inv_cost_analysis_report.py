# -*- coding: utf-8 -*-

from odoo import api, models


class MrpCostStructure(models.AbstractModel):
    _name = 'report.stock_adjustment_barcode.inv_cost_analysis_report'
    _description = 'Inventory Cost Analysis Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.adjustment.barcode'].browse(docids)
        return {'lines': docs.inv_adjustment_line_ids, 'currency': docs.currency_id}

class StockVariationReport(models.AbstractModel):
    _name = 'report.stock_adjustment_barcode.stock_variation_report'
    _description = 'Stock Variation Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.adjustment.barcode'].browse(docids)
        return {'lines': docs.inv_adjustment_line_ids, 'currency': docs.currency_id}