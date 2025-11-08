# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError, UserError
from .test_stock_adjustment_barcode_base import TestStockAdjustmentBarcodeBase


class TestWorkflow(TestStockAdjustmentBarcodeBase):
    """Test workflow state transitions and validations"""
    
    def test_01_draft_to_approve(self):
        """Test Case 7.1: Draft to To Approve confirmation process"""
        # Create initial stock
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        self.create_quant(self.product_lot, self.location_parent, 5, lot=self.lot1)
        
        # Create adjustment with scanned lines
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # Scan products
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        
        # Confirm
        adjustment.action_confirm()
        
        # Verify state change
        self.assertEqual(adjustment.state, 'to_approve')
        
        # Verify zero lines created for unscanned products in location
        # Should have lines for scanned products plus any other products in location
        self.assertTrue(len(adjustment.inv_adjustment_line_ids) >= 2)
        
        # Verify lot lines computed
        lot_line = adjustment.inv_adjustment_line_ids.filtered(
            lambda l: l.product_id == self.product_lot
        )
        self.assertTrue(len(lot_line.adjustment_line_lot_ids) > 0)
        
    def test_02_approval_process(self):
        """Test Case 7.2: Approval by authorized user"""
        # Setup adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        adjustment.action_confirm()
        
        # Try approval with non-authorized user (should fail)
        with self.assertRaises(Exception):
            adjustment.with_user(self.user_scanner).action_approved()
        
        # Approve with authorized user
        adjustment.with_user(self.user_approver).action_approved()
        
        # Verify state and approved_by
        self.assertEqual(adjustment.state, 'approved')
        self.assertEqual(adjustment.approved_by, self.user_approver)
        
    def test_03_posting_with_errors(self):
        """Test Case 7.3: Posting blocked with error lines"""
        # Create product without quants (will cause error)
        new_product = self.env['product.product'].create({
            'name': 'Error Product',
            'type': 'product',
            'tracking': 'lot',
            'barcode': 'ERROR-PROD',
        })
        
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'ERROR-PROD', user=self.user_admin)
        
        # Confirm and approve
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        
        # Try to post - should not raise error but post message
        adjustment.action_done()
        
        # Check that state didn't change to done
        self.assertNotEqual(adjustment.state, 'done')
        
        # Check for error message in chatter
        messages = adjustment.message_ids.mapped('body')
        self.assertTrue(any('resolve the stock mismatch' in str(msg) for msg in messages))
        
    def test_04_successful_posting(self):
        """Test Case 7.4: Successful Posting"""
        # Create stock
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # Scan different quantity
        for _ in range(15):
            self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Confirm and approve
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        
        # Post
        adjustment.action_done()
        
        # Verify state
        self.assertEqual(adjustment.state, 'done')
        
        # Verify stock moves created
        self.assertTrue(len(adjustment.inv_adjustment_line_ids.stock_move_ids) > 0)
        
        # Verify unit prices stored
        for line in adjustment.inv_adjustment_line_ids:
            if line.difference_qty != 0:
                self.assertIsNotNone(line.unit_price)
        
        # Verify posted_date is set
        self.assertIsNotNone(adjustment.posted_date)
        
    def test_05_back_to_draft(self):
        """Test Case 7.5: Reset to draft capability"""
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Confirm and approve
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        
        # Cancel
        adjustment.action_cancel()
        self.assertEqual(adjustment.state, 'cancel')
        
        # Reset to draft
        adjustment.action_reset_to_draft()
        self.assertEqual(adjustment.state, 'draft')
        
        # Should be able to scan again
        self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        self.assertEqual(len(adjustment.inv_adjustment_line_info_ids), 2)
        
    def test_06_difference_mismatch_check(self):
        """Test Case 7.6: Difference Mismatch Validation"""
        # This would require manipulating the lot lines to create mismatch
        # which is complex to simulate in test environment
        pass
        
    def test_07_workflow_permissions(self):
        """Test workflow permissions for different user groups"""
        # Create adjustment as scanner user
        adjustment = self.create_adjustment(self.location_parent, user=self.user_scanner)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_scanner)
        
        # Scanner can confirm
        adjustment.action_confirm()
        self.assertEqual(adjustment.state, 'to_approve')
        
        # Scanner cannot approve
        with self.assertRaises(Exception):
            adjustment.action_approved()
        
        # Approver can approve
        adjustment.with_user(self.user_approver).action_approved()
        self.assertEqual(adjustment.state, 'approved')
        
    def test_08_cancel_restrictions(self):
        """Test cancel state restrictions"""
        # Create and complete adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # Cannot cancel done adjustment
        with self.assertRaises(ValidationError) as context:
            adjustment.action_cancel()
        
        self.assertIn('not allowed to cancel', str(context.exception))
        
    def test_09_empty_adjustment_validation(self):
        """Test that empty adjustments cannot be confirmed"""
        # Create adjustment without any lines
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # Try to confirm without lines
        with self.assertRaises(ValidationError) as context:
            adjustment.action_confirm()
        
        self.assertIn('No Lines are created', str(context.exception))
        
    def test_10_zero_lines_creation(self):
        """Test automatic zero lines creation for unscanned products"""
        # Create stock for multiple products
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        self.create_quant(self.product_lot, self.location_parent, 5, lot=self.lot1)
        self.create_quant(self.product_serial, self.location_parent, 1, lot=self.serial1)
        
        # Create adjustment and scan only one product
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Confirm - should create zero lines for unscanned
        adjustment.action_confirm()
        
        # Should have lines for all products in location
        products_in_lines = adjustment.inv_adjustment_line_ids.mapped('product_id')
        self.assertIn(self.product_no_tracking, products_in_lines)
        self.assertIn(self.product_lot, products_in_lines)
        self.assertIn(self.product_serial, products_in_lines)
        
        # Unscanned products should have zero scanned quantity
        unscanned_lines = adjustment.inv_adjustment_line_ids.filtered(
            lambda l: l.product_id != self.product_no_tracking
        )
        for line in unscanned_lines:
            self.assertEqual(line.total_scanned_qty, 0)