# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo import fields
from datetime import datetime, timedelta


class TestStockAdjustmentBarcodeBase(TransactionCase):
    """Base test class with common setup for stock adjustment barcode tests"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test company
        cls.company = cls.env['res.company'].create({
            'name': 'Test Company',
        })
        
        # Create test users with different roles
        cls.user_admin = cls.env['res.users'].create({
            'name': 'Admin User',
            'login': 'admin_test',
            'email': 'admin@test.com',
            'company_id': cls.company.id,
            'company_ids': [(4, cls.company.id)],
            'groups_id': [(4, cls.env.ref('stock.group_stock_manager').id),
                         (4, cls.env.ref('stock_adjustment_barcode.approve_stock_adjustment_barcode_group').id)]
        })
        
        cls.user_scanner = cls.env['res.users'].create({
            'name': 'Scanner User',
            'login': 'scanner_test',
            'email': 'scanner@test.com',
            'company_id': cls.company.id,
            'company_ids': [(4, cls.company.id)],
            'groups_id': [(4, cls.env.ref('stock.group_stock_user').id)]
        })
        
        cls.user_scanner2 = cls.env['res.users'].create({
            'name': 'Scanner User 2',
            'login': 'scanner2_test',
            'email': 'scanner2@test.com',
            'company_id': cls.company.id,
            'company_ids': [(4, cls.company.id)],
            'groups_id': [(4, cls.env.ref('stock.group_stock_user').id)]
        })
        
        cls.user_approver = cls.env['res.users'].create({
            'name': 'Approver User',
            'login': 'approver_test',
            'email': 'approver@test.com',
            'company_id': cls.company.id,
            'company_ids': [(4, cls.company.id)],
            'groups_id': [(4, cls.env.ref('stock.group_stock_manager').id),
                         (4, cls.env.ref('stock_adjustment_barcode.approve_stock_adjustment_barcode_group').id)]
        })
        
        # Create warehouse and locations
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TWH',
            'company_id': cls.company.id,
        })
        
        cls.location_parent = cls.env['stock.location'].create({
            'name': 'Test Stock Location',
            'usage': 'internal',
            'location_id': cls.warehouse.lot_stock_id.id,
            'company_id': cls.company.id,
        })
        
        cls.location_child1 = cls.env['stock.location'].create({
            'name': 'Shelf 1',
            'usage': 'internal',
            'location_id': cls.location_parent.id,
            'company_id': cls.company.id,
        })
        
        cls.location_child2 = cls.env['stock.location'].create({
            'name': 'Shelf 2',
            'usage': 'internal',
            'location_id': cls.location_parent.id,
            'company_id': cls.company.id,
        })
        
        # Create product categories
        cls.product_category = cls.env['product.category'].create({
            'name': 'Test Category',
        })
        
        # Create products with different configurations
        cls.product_lot = cls.env['product.product'].create({
            'name': 'Product with Lot Tracking',
            'type': 'product',
            'categ_id': cls.product_category.id,
            'barcode': 'PROD-LOT-001',
            'tracking': 'lot',
            'default_code': 'PROD-LOT',
            'standard_price': 100.0,
        })
        
        cls.product_no_tracking = cls.env['product.product'].create({
            'name': 'Product No Tracking',
            'type': 'product',
            'categ_id': cls.product_category.id,
            'barcode': 'PROD-NO-001',
            'tracking': 'none',
            'default_code': 'PROD-NO',
            'standard_price': 50.0,
        })
        
        cls.product_serial = cls.env['product.product'].create({
            'name': 'Product with Serial Tracking',
            'type': 'product',
            'categ_id': cls.product_category.id,
            'barcode': 'PROD-SERIAL-001',
            'tracking': 'serial',
            'default_code': 'PROD-SERIAL',
            'standard_price': 200.0,
        })
        
        cls.product_no_barcode = cls.env['product.product'].create({
            'name': 'Product without Barcode',
            'type': 'product',
            'categ_id': cls.product_category.id,
            'tracking': 'none',
            'default_code': 'PROD-NO-BARCODE',
            'standard_price': 75.0,
        })
        
        # Create lots for lot-tracked product with different in_dates for FIFO
        cls.lot1 = cls.env['stock.lot'].create({
            'name': 'LOT001',
            'product_id': cls.product_lot.id,
            'company_id': cls.company.id,
        })
        
        cls.lot2 = cls.env['stock.lot'].create({
            'name': 'LOT002',
            'product_id': cls.product_lot.id,
            'company_id': cls.company.id,
        })
        
        cls.lot3 = cls.env['stock.lot'].create({
            'name': 'LOT003',
            'product_id': cls.product_lot.id,
            'company_id': cls.company.id,
        })
        
        # Create serial numbers
        cls.serial1 = cls.env['stock.lot'].create({
            'name': 'SERIAL001',
            'product_id': cls.product_serial.id,
            'company_id': cls.company.id,
        })
        
    def setUp(self):
        super().setUp()
        # Clear any existing quants before each test
        self.env['stock.quant'].search([
            ('location_id', 'child_of', self.warehouse.lot_stock_id.id)
        ]).sudo().unlink()
        
    def create_quant(self, product, location, quantity, lot=None, in_date=None):
        """Helper method to create stock quants"""
        quant_vals = {
            'product_id': product.id,
            'location_id': location.id,
            'quantity': quantity,
            'company_id': self.company.id,
        }
        if lot:
            quant_vals['lot_id'] = lot.id
        if in_date:
            quant_vals['in_date'] = in_date
        return self.env['stock.quant'].sudo().create(quant_vals)
    
    def create_adjustment(self, location, user=None, state='draft'):
        """Helper method to create stock adjustment"""
        if not user:
            user = self.user_admin
        adjustment = self.env['stock.adjustment.barcode'].with_user(user).create({
            'location_id': location.id,
            'company_id': self.company.id,
        })
        if state != 'draft':
            # Progress through states as needed
            if state in ['to_approve', 'approved', 'done']:
                adjustment.action_confirm()
            if state in ['approved', 'done']:
                adjustment.with_user(self.user_approver).action_approved()
            if state == 'done':
                adjustment.action_done()
        return adjustment
    
    def simulate_barcode_scan(self, adjustment, barcode, user=None):
        """Helper method to simulate barcode scanning"""
        if not user:
            user = self.env.user
        return adjustment.with_user(user).on_barcode_scanned(barcode)
    
    def create_stock_move(self, product, location_from, location_to, quantity, lot=None):
        """Helper method to create and validate stock move"""
        move = self.env['stock.move'].create({
            'name': f'Test Move {product.name}',
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': product.uom_id.id,
            'location_id': location_from.id,
            'location_dest_id': location_to.id,
            'company_id': self.company.id,
        })
        move._action_confirm()
        move._action_assign()
        
        if lot:
            move.move_line_ids.write({
                'lot_id': lot.id,
                'qty_done': quantity,
            })
        else:
            move.move_line_ids.write({
                'qty_done': quantity,
            })
        
        move._action_done()
        return move
    
    def assertQuantity(self, product, location, expected_qty, lot=None, msg=None):
        """Helper assertion for checking stock quantities"""
        domain = [
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
        ]
        if lot:
            domain.append(('lot_id', '=', lot.id))
        
        quants = self.env['stock.quant'].search(domain)
        actual_qty = sum(quants.mapped('quantity'))
        
        if msg:
            self.assertAlmostEqual(actual_qty, expected_qty, places=2, msg=msg)
        else:
            self.assertAlmostEqual(actual_qty, expected_qty, places=2,
                                  msg=f"Expected {expected_qty} but got {actual_qty} for {product.name} in {location.name}")
    
    def progress_workflow(self, adjustment, target_state):
        """Helper to progress adjustment through workflow states"""
        if target_state == 'to_approve' and adjustment.state == 'draft':
            adjustment.action_confirm()
        elif target_state == 'approved' and adjustment.state == 'to_approve':
            adjustment.with_user(self.user_approver).action_approved()
        elif target_state == 'done' and adjustment.state == 'approved':
            adjustment.action_done()
        elif target_state == 'cancel':
            adjustment.action_cancel()
        
        return adjustment