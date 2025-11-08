# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from .test_stock_adjustment_barcode_base import TestStockAdjustmentBarcodeBase


class TestBarcodeScanning(TestStockAdjustmentBarcodeBase):
    """Test barcode scanning functionality"""
    
    def test_01_product_barcode_scanning(self):
        """Test Case 1.1: Product Barcode Scanning"""
        # Create adjustment in draft state
        adjustment = self.create_adjustment(self.location_parent, user=self.user_scanner)
        
        # Scan product barcode
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner)
        
        # Verify line creation
        self.assertEqual(len(adjustment.inv_adjustment_line_info_ids), 1)
        line_info = adjustment.inv_adjustment_line_info_ids[0]
        self.assertEqual(line_info.product_id, self.product_no_tracking)
        self.assertEqual(line_info.scanned_qty, 1.0)
        self.assertEqual(line_info.scanned_user_id, self.user_scanner)
        
    def test_02_multiple_scans_same_product(self):
        """Test Case 1.2: Multiple Scans Same Product"""
        adjustment = self.create_adjustment(self.location_parent, user=self.user_scanner)
        
        # Scan same product twice
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner)
        
        # Should increment quantity on same line info
        self.assertEqual(len(adjustment.inv_adjustment_line_info_ids), 1)
        self.assertEqual(adjustment.inv_adjustment_line_info_ids[0].scanned_qty, 2.0)
        
        # Verify adjustment line is created/updated
        adjustment_lines = self.env['stock.adjustment.barcode.line'].search([
            ('inv_adjustment_id', '=', adjustment.id)
        ])
        self.assertEqual(len(adjustment_lines), 1)
        self.assertEqual(adjustment_lines[0].total_scanned_qty, 2.0)
        
    def test_03_user_recording(self):
        """Test Case 1.3: User Recording"""
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # User A scans product
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner)
        
        # User B scans same product
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner2)
        
        # Check line info records - should have separate records
        line_infos = adjustment.inv_adjustment_line_info_ids
        self.assertEqual(len(line_infos), 2)
        
        # Verify users are recorded correctly
        users = line_infos.mapped('scanned_user_id')
        self.assertIn(self.user_scanner, users)
        self.assertIn(self.user_scanner2, users)
        
        # Each user should have their own line info
        user1_lines = line_infos.filtered(lambda l: l.scanned_user_id == self.user_scanner)
        user2_lines = line_infos.filtered(lambda l: l.scanned_user_id == self.user_scanner2)
        self.assertEqual(len(user1_lines), 1)
        self.assertEqual(len(user2_lines), 1)
        
    def test_04_user_visibility(self):
        """Test Case 1.4: User Visibility - users only see their own scans"""
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # User A scans products
        adjustment_user1 = adjustment.with_user(self.user_scanner)
        self.simulate_barcode_scan(adjustment_user1, 'PROD-NO-001', user=self.user_scanner)
        self.simulate_barcode_scan(adjustment_user1, 'PROD-LOT-001', user=self.user_scanner)
        
        # User B scans products
        adjustment_user2 = adjustment.with_user(self.user_scanner2)
        self.simulate_barcode_scan(adjustment_user2, 'PROD-NO-001', user=self.user_scanner2)
        
        # Check visibility - User A sees only their scans
        visible_lines_user1 = adjustment_user1.inv_adjustment_line_info_ids
        self.assertEqual(len(visible_lines_user1), 2)
        self.assertTrue(all(line.scanned_user_id == self.user_scanner for line in visible_lines_user1))
        
        # User B sees only their scans
        visible_lines_user2 = adjustment_user2.inv_adjustment_line_info_ids
        self.assertEqual(len(visible_lines_user2), 1)
        self.assertTrue(all(line.scanned_user_id == self.user_scanner2 for line in visible_lines_user2))
        
        # Admin should see all scans
        all_lines = adjustment.with_user(self.user_admin).inv_adjustment_line_info_ids
        self.assertEqual(len(all_lines), 3)
        
    def test_05_invalid_barcode(self):
        """Test Case 1.5: Invalid Barcode"""
        adjustment = self.create_adjustment(self.location_parent, user=self.user_scanner)
        
        # Scan non-existent barcode
        with self.assertRaises(UserError) as context:
            self.simulate_barcode_scan(adjustment, 'INVALID-BARCODE-999', user=self.user_scanner)
        
        self.assertIn('not available in the system', str(context.exception))
        
    def test_06_scan_in_non_draft_state(self):
        """Test Case 1.6: Scan in Non-Draft State"""
        # Create and confirm adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # Add initial scan
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Confirm adjustment (moves to to_approve state)
        adjustment.action_confirm()
        self.assertEqual(adjustment.state, 'to_approve')
        
        # Try to scan in non-draft state
        with self.assertRaises(ValidationError) as context:
            self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        self.assertIn("You can only scan lines in the 'draft' state", str(context.exception))
        
    def test_07_scan_lot_tracked_product(self):
        """Test scanning lot-tracked product"""
        adjustment = self.create_adjustment(self.location_parent, user=self.user_scanner)
        
        # Create initial stock for lot-tracked product
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot1)
        
        # Scan lot-tracked product
        self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_scanner)
        
        # Verify line creation
        self.assertEqual(len(adjustment.inv_adjustment_line_info_ids), 1)
        line_info = adjustment.inv_adjustment_line_info_ids[0]
        self.assertEqual(line_info.product_id, self.product_lot)
        self.assertEqual(line_info.scanned_qty, 1.0)
        
        # Adjustment line should be created
        adj_lines = self.env['stock.adjustment.barcode.line'].search([
            ('inv_adjustment_id', '=', adjustment.id)
        ])
        self.assertEqual(len(adj_lines), 1)
        self.assertEqual(adj_lines[0].product_id, self.product_lot)
        
    def test_08_scan_serial_tracked_product(self):
        """Test scanning serial-tracked product"""
        adjustment = self.create_adjustment(self.location_parent, user=self.user_scanner)
        
        # Scan serial-tracked product
        self.simulate_barcode_scan(adjustment, 'PROD-SERIAL-001', user=self.user_scanner)
        
        # Verify line creation
        self.assertEqual(len(adjustment.inv_adjustment_line_info_ids), 1)
        line_info = adjustment.inv_adjustment_line_info_ids[0]
        self.assertEqual(line_info.product_id, self.product_serial)
        self.assertEqual(line_info.scanned_qty, 1.0)
        
    def test_09_total_quantity_display(self):
        """Test that main screen shows total quantity scanned by all users"""
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # Multiple users scan same product
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner2)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner2)
        
        # Check adjustment line shows total
        adj_lines = self.env['stock.adjustment.barcode.line'].search([
            ('inv_adjustment_id', '=', adjustment.id)
        ])
        self.assertEqual(len(adj_lines), 1)
        self.assertEqual(adj_lines[0].total_scanned_qty, 4.0)
        
    def test_10_multiple_products_scanning(self):
        """Test scanning multiple different products"""
        adjustment = self.create_adjustment(self.location_parent, user=self.user_scanner)
        
        # Scan different products
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner)
        self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_scanner)
        self.simulate_barcode_scan(adjustment, 'PROD-SERIAL-001', user=self.user_scanner)
        
        # Should create separate line infos
        self.assertEqual(len(adjustment.inv_adjustment_line_info_ids), 3)
        
        # Should create separate adjustment lines
        adj_lines = self.env['stock.adjustment.barcode.line'].search([
            ('inv_adjustment_id', '=', adjustment.id)
        ])
        self.assertEqual(len(adj_lines), 3)
        
        # Verify products
        products = adj_lines.mapped('product_id')
        self.assertIn(self.product_no_tracking, products)
        self.assertIn(self.product_lot, products)
        self.assertIn(self.product_serial, products)
        
    def test_11_duplicate_adjustment_same_location(self):
        """Test that only one active adjustment can exist per location"""
        # Create first adjustment
        adjustment1 = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # Try to create second adjustment for same location
        with self.assertRaises(ValidationError) as context:
            adjustment2 = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        self.assertIn('You can only have one active adjustment for a location', str(context.exception))
        
        # Complete first adjustment
        self.simulate_barcode_scan(adjustment1, 'PROD-NO-001', user=self.user_admin)
        adjustment1.action_confirm()
        adjustment1.with_user(self.user_approver).action_approved()
        adjustment1.action_done()
        
        # Now should be able to create new adjustment
        adjustment3 = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.assertEqual(adjustment3.state, 'draft')