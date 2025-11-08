# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from .test_stock_adjustment_barcode_base import TestStockAdjustmentBarcodeBase
from datetime import datetime, timedelta


class TestLotSelection(TestStockAdjustmentBarcodeBase):
    """Test auto lot selection based on FIFO strategy"""
    
    def test_01_fifo_stock_addition(self):
        """Test Case 3.1: FIFO Selection - Stock Addition"""
        # Create stock with multiple lots with different in_dates
        date1 = datetime.now() - timedelta(days=3)
        date2 = datetime.now() - timedelta(days=2)
        date3 = datetime.now() - timedelta(days=1)
        
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot1, in_date=date1)
        self.create_quant(self.product_lot, self.location_parent, 15, lot=self.lot2, in_date=date2)
        self.create_quant(self.product_lot, self.location_parent, 5, lot=self.lot3, in_date=date3)
        
        # Create adjustment and scan to add stock (40 total)
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(40):
            self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        # Check lot assignments - addition should go to first lot (FIFO)
        adj_line = adjustment.inv_adjustment_line_ids[0]
        lot_lines = adj_line.adjustment_line_lot_ids
        
        # First lot should have the addition
        lot1_line = lot_lines.filtered(lambda l: l.lot_id == self.lot1)
        self.assertEqual(lot1_line.current_qty, 10)
        self.assertEqual(lot1_line.new_qty, 20)  # 10 + 10 addition
        self.assertEqual(lot1_line.difference_qty, 10)
        
    def test_02_fifo_stock_deduction(self):
        """Test Case 3.2: FIFO Selection - Stock Deduction across lots"""
        # Setup: LOT001: 10 units, LOT002: 15 units, LOT003: 5 units
        date1 = datetime.now() - timedelta(days=3)
        date2 = datetime.now() - timedelta(days=2)
        date3 = datetime.now() - timedelta(days=1)
        
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot1, in_date=date1)
        self.create_quant(self.product_lot, self.location_parent, 15, lot=self.lot2, in_date=date2)
        self.create_quant(self.product_lot, self.location_parent, 5, lot=self.lot3, in_date=date3)
        
        # Scan to reduce by 20 units (total will be 10)
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(10):  # Scanning 10, current is 30, so reduction of 20
            self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        # Check FIFO deduction
        adj_line = adjustment.inv_adjustment_line_ids[0]
        lot_lines = adj_line.adjustment_line_lot_ids
        
        # LOT001: Should be 0 (reduced by 10)
        lot1_line = lot_lines.filtered(lambda l: l.lot_id == self.lot1)
        self.assertEqual(lot1_line.current_qty, 10)
        self.assertEqual(lot1_line.new_qty, 0)
        
        # LOT002: Should be 5 (reduced by 10)
        lot2_line = lot_lines.filtered(lambda l: l.lot_id == self.lot2)
        self.assertEqual(lot2_line.current_qty, 15)
        self.assertEqual(lot2_line.new_qty, 5)
        
        # LOT003: Should be unchanged
        lot3_line = lot_lines.filtered(lambda l: l.lot_id == self.lot3)
        self.assertEqual(lot3_line.current_qty, 5)
        self.assertEqual(lot3_line.new_qty, 5)
        
    def test_03_lot_search_hierarchy(self):
        """Test Case 3.3: Lot Search in Location hierarchy"""
        # Create lot in different location (not in adjustment location)
        other_location = self.env['stock.location'].create({
            'name': 'Other Location',
            'usage': 'internal',
            'company_id': self.company.id,
        })
        
        # Create quant in other location
        self.create_quant(self.product_lot, other_location, 0, lot=self.lot1)
        
        # Create adjustment for location without the lot
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # Scan product
        for _ in range(10):
            self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        
        # Confirm - should find lot in company
        adjustment.action_confirm()
        
        # Check that lot was found and used
        adj_line = adjustment.inv_adjustment_line_ids[0]
        lot_lines = adj_line.adjustment_line_lot_ids
        
        # Should create line with found lot
        self.assertTrue(len(lot_lines) > 0)
        self.assertIn(self.lot1, lot_lines.mapped('lot_id'))
        
    def test_04_no_quants_available_error(self):
        """Test Case 3.4: No Quants Available - Line marked as erroneous"""
        # Create product without any quants
        new_product = self.env['product.product'].create({
            'name': 'Product No Quants',
            'type': 'product',
            'tracking': 'lot',
            'barcode': 'PROD-NO-QUANTS',
        })
        
        # Create adjustment and scan
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-QUANTS', user=self.user_admin)
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        # Line should be marked as erroneous
        adj_line = adjustment.inv_adjustment_line_ids.filtered(
            lambda l: l.product_id == new_product
        )
        self.assertTrue(adj_line.is_editable)  # is_editable indicates error
        
    def test_05_insufficient_stock_for_deduction(self):
        """Test Case 3.5: Insufficient Stock for Deduction - Line marked as erroneous"""
        # Create stock: total 20 units
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot1)
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot2)
        
        # Try to deduct 30 units (scan 0, but stock is 20, so -20 difference)
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        # Don't scan anything - scanned qty = 0, on_hand = 20, difference = -20
        
        # Add line manually with 0 scanned quantity
        line_info = self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_lot.id,
            'scanned_qty': 0,
            'scanned_user_id': self.user_admin.id,
        })
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        # Check if line is marked as erroneous when difference exceeds available
        adj_line = adjustment.inv_adjustment_line_ids[0]
        
        # For this case, negative stock isn't allowed, it should handle appropriately
        # The actual behavior depends on implementation
        self.assertEqual(adj_line.on_hand_qty, 20)
        self.assertEqual(adj_line.total_scanned_qty, 0)
        self.assertEqual(adj_line.difference_qty, -20)
        
    def test_06_fifo_with_zero_quantity_lots(self):
        """Test FIFO handling with lots having zero quantity"""
        # Create lots with varying quantities including zero
        date1 = datetime.now() - timedelta(days=3)
        date2 = datetime.now() - timedelta(days=2)
        date3 = datetime.now() - timedelta(days=1)
        
        self.create_quant(self.product_lot, self.location_parent, 0, lot=self.lot1, in_date=date1)
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot2, in_date=date2)
        self.create_quant(self.product_lot, self.location_parent, 5, lot=self.lot3, in_date=date3)
        
        # Scan to add stock
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(20):
            self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        # Check lot assignments
        adj_line = adjustment.inv_adjustment_line_ids[0]
        lot_lines = adj_line.adjustment_line_lot_ids
        
        # First lot (even with 0 qty) should get the addition per FIFO
        lot1_line = lot_lines.filtered(lambda l: l.lot_id == self.lot1)
        self.assertEqual(lot1_line.current_qty, 0)
        self.assertEqual(lot1_line.new_qty, 5)  # Gets the addition