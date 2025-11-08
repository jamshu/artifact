# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    def _validate_accounting_entries(self):
        """
        Validates and creates accounting entries for inventory adjustments.
        Override to set accounting date from Inventory Adjustment Barcode.

        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        if not self.stock_move_id.inv_adjustment_line_id:
            return super()._validate_accounting_entries()

        am_vals = []
        for svl in self:
            if not svl.with_company(svl.company_id).product_id.valuation == 'real_time':
                continue
            if svl.currency_id.is_zero(svl.value):
                continue
            move = svl.stock_move_id
            if not move:
                move = svl.stock_valuation_layer_id.stock_move_id
            am_vals += move.with_company(svl.company_id)._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
        if am_vals:
            if move.inv_adjustment_line_id.inv_adjustment_id:
                force_accounting_date = move.inv_adjustment_line_id.inv_adjustment_id.force_accounting_date
                for entry in am_vals:
                    entry['date'] = force_accounting_date
            account_moves = self.env['account.move'].sudo().create(am_vals)
            account_moves._post()
        for svl in self:
            if svl.company_id.anglo_saxon_accounting:
                svl.stock_move_id._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=svl.product_id)
