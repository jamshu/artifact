# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from .test_stock_adjustment_barcode_base import TestStockAdjustmentBarcodeBase
from datetime import datetime, timedelta


class TestNegativeStock(TestStockAdjustmentBarcodeBase):
    """Test negative stock handling functionality"""
    
    def test_01_zero_negative_stock(self):
        """Test Case 2.1: Verify negative stock becomes zero"""
        # Create negative stock (-5 quantity)
        self.create_quant(self.product_no_tracking, self.location_parent, -5)
        
        # Create adjustment and scan product 10 times
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(10):
            self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        # Check adjustment line
        adj_line = adjustment.inv_adjustment_line_ids[0]
        self.assertEqual(adj_line.on_hand_qty, -5)  # Current stock
        self.assertEqual(adj_line.total_scanned_qty, 10)  # Scanned quantity
        self.assertEqual(adj_line.difference_qty, 15)  # Difference
        
        # Approve and post adjustment
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # Verify final quantity is 10 (negative stock became 0, then added 10)
        self.assertQuantity(self.product_no_tracking, self.location_parent, 10)
        
    def test_02_multiple_negative_quants(self):
        """Test Case 2.2: Verify all negative quants handled"""
        # Create multiple lots with negative quantities
        self.create_quant(self.product_lot, self.location_parent, -3, lot=self.lot1)
        self.create_quant(self.product_lot, self.location_parent, -2, lot=self.lot2)
        self.create_quant(self.product_lot, self.location_parent, -5, lot=self.lot3)
        
        # Create adjustment and scan positive quantity
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(20):
            self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        # Check lot lines after confirmation
        adj_line = adjustment.inv_adjustment_line_ids[0]
        lot_lines = adj_line.adjustment_line_lot_ids
        
        # All negative quants should be marked to become zero
        for lot_line in lot_lines:
            if lot_line.current_qty < 0:
                # Negative quantities should be set to 0 or positive
                self.assertGreaterEqual(lot_line.new_qty, 0)
        
        # Approve and post
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # Verify all lots have non-negative quantities
        self.assertGreaterEqual(sum(self.env['stock.quant'].search([
            ('product_id', '=', self.product_lot.id),
            ('location_id', '=', self.location_parent.id),
            ('lot_id', '=', self.lot1.id)
        ]).mapped('quantity')), 0)
        
        self.assertGreaterEqual(sum(self.env['stock.quant'].search([
            ('product_id', '=', self.product_lot.id),
            ('location_id', '=', self.location_parent.id),
            ('lot_id', '=', self.lot2.id)
        ]).mapped('quantity')), 0)
        
        self.assertGreaterEqual(sum(self.env['stock.quant'].search([
            ('product_id', '=', self.product_lot.id),
            ('location_id', '=', self.location_parent.id),
            ('lot_id', '=', self.lot3.id)
        ]).mapped('quantity')), 0)
        
        # Total quantity should be 20
        total_qty = sum(self.env['stock.quant'].search([
            ('product_id', '=', self.product_lot.id),
            ('location_id', '=', self.location_parent.id)
        ]).mapped('quantity'))
        self.assertAlmostEqual(total_qty, 20, places=2)
        
    def test_03_mixed_positive_negative_stock(self):
        """Test handling of mixed positive and negative stock"""
        # Create mixed stock situation
        self.create_quant(self.product_lot, self.location_parent, -5, lot=self.lot1)
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot2)
        self.create_quant(self.product_lot, self.location_parent, -3, lot=self.lot3)
        
        # Total current stock = -5 + 10 + (-3) = 2
        
        # Create adjustment and scan 15 units
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(15):
            self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        # Check adjustment calculations
        adj_line = adjustment.inv_adjustment_line_ids[0]
        self.assertEqual(adj_line.on_hand_qty, 2)  # Current total
        self.assertEqual(adj_line.total_scanned_qty, 15)  # Scanned
        self.assertEqual(adj_line.difference_qty, 13)  # Difference
        
        # Approve and post
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # Verify final total is 15
        total_qty = sum(self.env['stock.quant'].search([
            ('product_id', '=', self.product_lot.id),
            ('location_id', '=', self.location_parent.id)
        ]).mapped('quantity'))
        self.assertAlmostEqual(total_qty, 15, places=2)
        
    def test_04_all_negative_quants_first_lot_assignment(self):
        """Test that when all quants are negative, scanned qty is assigned to first lot"""
        # Create all negative quants with specific dates for ordering
        date1 = datetime.now() - timedelta(days=3)
        date2 = datetime.now() - timedelta(days=2)
        date3 = datetime.now() - timedelta(days=1)
        
        self.create_quant(self.product_lot, self.location_parent, -5, lot=self.lot1, in_date=date1)
        self.create_quant(self.product_lot, self.location_parent, -3, lot=self.lot2, in_date=date2)
        self.create_quant(self.product_lot, self.location_parent, -2, lot=self.lot3, in_date=date3)
        
        # Create adjustment and scan 20 units
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(20):
            self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        # Check lot assignments
        adj_line = adjustment.inv_adjustment_line_ids[0]
        lot_lines = adj_line.adjustment_line_lot_ids.sorted('lot_id')
        
        # First lot should get the full scanned quantity
        lot1_line = lot_lines.filtered(lambda l: l.lot_id == self.lot1)
        self.assertEqual(lot1_line.new_qty, 20)  # All scanned qty to first lot
        
        # Other lots should become zero
        lot2_line = lot_lines.filtered(lambda l: l.lot_id == self.lot2)
        self.assertEqual(lot2_line.new_qty, 0)
        
        lot3_line = lot_lines.filtered(lambda l: l.lot_id == self.lot3)
        self.assertEqual(lot3_line.new_qty, 0)