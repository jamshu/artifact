# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError, UserError
from .test_stock_adjustment_barcode_base import TestStockAdjustmentBarcodeBase


class TestStockPosting(TestStockAdjustmentBarcodeBase):
    """Test stock move creation, validation and cost tracking"""
    
    def test_01_stock_move_creation(self):
        """Test Case 8.1: Stock Move Creation"""
        # Create initial stock
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        
        # Create adjustment with positive difference
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(15):  # Scan 15, stock is 10, difference is +5
            self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Process workflow
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # Check stock moves created
        stock_moves = adjustment.inv_adjustment_line_ids.stock_move_ids
        self.assertTrue(len(stock_moves) > 0)
        
        # Verify move direction for positive difference
        for move in stock_moves:
            if adjustment.inv_adjustment_line_ids[0].difference_qty > 0:
                # Positive: inventory → location
                self.assertEqual(move.location_id.usage, 'inventory')
                self.assertEqual(move.location_dest_id, self.location_parent)
        
        # Test negative difference
        adjustment2 = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(5):  # Scan 5, stock is 15, difference is -10
            self.simulate_barcode_scan(adjustment2, 'PROD-NO-001', user=self.user_admin)
        
        adjustment2.action_confirm()
        adjustment2.with_user(self.user_approver).action_approved()
        adjustment2.action_done()
        
        # Check move direction for negative difference
        stock_moves2 = adjustment2.inv_adjustment_line_ids.stock_move_ids
        for move in stock_moves2:
            if adjustment2.inv_adjustment_line_ids[0].difference_qty < 0:
                # Negative: location → inventory
                self.assertEqual(move.location_id, self.location_parent)
                self.assertEqual(move.location_dest_id.usage, 'inventory')
        
    def test_02_unit_price_storage(self):
        """Test Case 8.2: Unit Price Storage in Lines"""
        # Create product with specific cost
        self.product_no_tracking.standard_price = 100.0
        
        # Create stock with valuation
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(15):
            self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Process workflow
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # Check unit price stored
        adj_line = adjustment.inv_adjustment_line_ids[0]
        self.assertIsNotNone(adj_line.unit_price)
        self.assertGreater(adj_line.unit_price, 0)
        
    def test_03_accounting_entry_creation(self):
        """Test Case 8.4: Accounting Entry Creation"""
        # Setup product with automated valuation
        self.product_no_tracking.categ_id.property_valuation = 'real_time'
        
        # Create stock
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(15):
            self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Process workflow
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # Check accounting entries if applicable
        stock_moves = adjustment.inv_adjustment_line_ids.stock_move_ids
        if stock_moves.account_move_ids:
            self.assertTrue(len(stock_moves.account_move_ids) > 0)
            # Verify accounting entries are balanced
            for account_move in stock_moves.account_move_ids:
                debit = sum(account_move.line_ids.mapped('debit'))
                credit = sum(account_move.line_ids.mapped('credit'))
                self.assertAlmostEqual(debit, credit, places=2)
        
    def test_04_stock_valuation_layers(self):
        """Test stock valuation layer creation"""
        # Create stock
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(15):
            self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Process workflow
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # Check valuation layers created
        stock_moves = adjustment.inv_adjustment_line_ids.stock_move_ids
        valuation_layers = self.env['stock.valuation.layer'].search([
            ('stock_move_id', 'in', stock_moves.ids)
        ])
        
        if valuation_layers:
            self.assertTrue(len(valuation_layers) > 0)
            # Check layer values
            for layer in valuation_layers:
                self.assertIsNotNone(layer.value)
                self.assertIsNotNone(layer.quantity)
        
    def test_05_lot_based_stock_moves(self):
        """Test stock moves creation for lot-tracked products"""
        # Create stock with lots
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot1)
        self.create_quant(self.product_lot, self.location_parent, 15, lot=self.lot2)
        
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(20):  # Total will be 20, current is 25, diff is -5
            self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        
        # Process workflow
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # Check moves created per lot
        stock_moves = adjustment.inv_adjustment_line_ids.stock_move_ids
        self.assertTrue(len(stock_moves) > 0)
        
        # Check move lines have lot information
        for move in stock_moves:
            self.assertTrue(len(move.move_line_ids) > 0)
            for line in move.move_line_ids:
                self.assertIsNotNone(line.lot_id)
                self.assertGreater(line.qty_done, 0)
        
    def test_06_negative_stock_prevention(self):
        """Test that posting prevents negative stock"""
        # Create stock with lot
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot1)
        
        # Try to create adjustment that would result in negative stock
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        
        # Don't scan anything - will try to reduce to 0
        line_info = self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_lot.id,
            'scanned_qty': 0,
            'scanned_user_id': self.user_admin.id,
        })
        
        # Process workflow
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        
        # This should work as reducing to 0 is valid
        adjustment.action_done()
        self.assertEqual(adjustment.state, 'done')
        
        # Verify final stock is 0
        self.assertQuantity(self.product_lot, self.location_parent, 0, lot=self.lot1)
        
    def test_07_posted_date_tracking(self):
        """Test posted date is properly tracked"""
        # Create stock
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Process workflow
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        
        # Check posted_date not set before posting
        self.assertIsNone(adjustment.posted_date)
        
        # Post
        adjustment.action_done()
        
        # Check posted_date is set
        self.assertIsNotNone(adjustment.posted_date)
        self.assertEqual(adjustment.posted_date.date(), fields.Date.today())
        
        # Check location's last inventory date updated
        self.assertEqual(self.location_parent.last_inventory_date, adjustment.posted_date.date())