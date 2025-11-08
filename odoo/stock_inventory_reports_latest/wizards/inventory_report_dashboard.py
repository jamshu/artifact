# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InventoryReportDashboard(models.TransientModel):
    """Main dashboard wizard to access inventory reports"""
    _name = 'inventory.report.dashboard'
    _description = 'Inventory Report Dashboard'

    name = fields.Char(string='Dashboard', default='Inventory Reports Dashboard', readonly=True)

    def action_open_scrap_report(self):
        """Open the Scrap Report wizard"""
        return {
            'name': 'Scrap Report',
            'type': 'ir.actions.act_window',
            'res_model': 'scrap.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_open_return_report(self):
        """Open the Return Report wizard"""
        return {
            'name': 'Return Report',
            'type': 'ir.actions.act_window',
            'res_model': 'return.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
