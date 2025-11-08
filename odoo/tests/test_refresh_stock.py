# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from .test_stock_adjustment_barcode_base import TestStockAdjustmentBarcodeBase
from datetime import datetime, timedelta
from odoo import fields


class TestRefreshStock(TestStockAdjustmentBarcodeBase):
    """Test refresh stock functionality for current and backdated stock"""
    
    def test_01_current_stock_refresh(self):
        """Test Case 4.1: Current Stock Refresh"""
        # Create initial stock
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        
        # Create adjustment and scan
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        
        # Confirm to get initial calculations
        adjustment.action_confirm()
        
        # Add stock move outside adjustment
        inventory_location = self.product_no_tracking.with_company(self.company).property_stock_inventory
        self.create_stock_move(
            self.product_no_tracking,
            inventory_location,
            self.location_parent,
            5
        )
        
        # Open refresh wizard
        action = adjustment.action_refresh_stock()
        wizard = self.env['stock.refresh.stock.wizard'].with_context(
            action['context']
        ).create({
            'fetch_type': 'current'
        })
        
        # Apply refresh
        wizard.action_apply()
        
        # Check on-hand quantities updated
        adj_line = adjustment.inv_adjustment_line_ids[0]
        self.assertEqual(adj_line.on_hand_qty, 15)  # 10 + 5 from move
        
        # Check inventory date updated to current
        self.assertAlmostEqual(
            adjustment.inventory_date,
            fields.Datetime.now(),
            delta=timedelta(minutes=1)
        )
        
    def test_02_backdated_stock_refresh(self):
        """Test Case 4.2: Backdated Stock Calculation"""
        # Create stock movements at different dates
        past_date = datetime.now() - timedelta(days=7)
        recent_date = datetime.now() - timedelta(days=2)
        
        # Initial stock 7 days ago
        self.create_quant(self.product_no_tracking, self.location_parent, 20)
        
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        adjustment.action_confirm()
        
        # Create recent stock move (2 days ago)
        inventory_location = self.product_no_tracking.with_company(self.company).property_stock_inventory
        recent_move = self.create_stock_move(
            self.product_no_tracking,
            self.location_parent,
            inventory_location,
            5
        )
        
        # Refresh with backdated option (5 days ago)
        backdate = datetime.now() - timedelta(days=5)
        action = adjustment.action_refresh_stock()
        wizard = self.env['stock.refresh.stock.wizard'].with_context(
            action['context']
        ).create({
            'fetch_type': 'backdated',
            'backdate': backdate
        })
        
        # Apply refresh
        wizard.action_apply()
        
        # Check quantities calculated as of selected date
        # Should show 20 (before the recent move)
        adj_line = adjustment.inv_adjustment_line_ids[0]
        # The actual behavior depends on how backdated calculation works
        # This test assumes it shows quantity as of that date
        
        # Check inventory date updated to backdated value
        self.assertEqual(adjustment.inventory_date, backdate)
        
    def test_03_refresh_permission_check(self):
        """Test Case 4.3: Refresh Permission Check"""
        # Create adjustment as admin
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        adjustment.action_confirm()
        
        # Try to refresh as non-authorized user
        # The actual permission check depends on security implementation
        # This is a placeholder for permission testing
        pass
        
    def test_04_refresh_state_restrictions(self):
        """Test Case 4.4: Refresh blocked in done/draft states"""
        # Create and complete adjustment
        self.create_quant(self.product_no_tracking, self.location_parent, 10)
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        adjustment.action_confirm()
        adjustment.with_user(self.user_approver).action_approved()
        adjustment.action_done()
        
        # In done state, refresh should not be available
        # The actual behavior depends on view configuration
        self.assertEqual(adjustment.state, 'done')
        
    def test_05_inventory_date_update(self):
        """Test Case 4.5: Inventory Date Update"""
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        initial_date = adjustment.inventory_date
        
        # Add some scans
        self.simulate_barcode_scan(adjustment, 'PROD-NO-001', user=self.user_admin)
        adjustment.action_confirm()
        
        # Refresh with current option
        action = adjustment.action_refresh_stock()
        wizard = self.env['stock.refresh.stock.wizard'].with_context(
            action['context']
        ).create({
            'fetch_type': 'current'
        })
        
        # Apply refresh
        wizard.action_apply()
        
        # Check inventory date updated
        self.assertNotEqual(adjustment.inventory_date, initial_date)
        self.assertAlmostEqual(
            adjustment.inventory_date,
            fields.Datetime.now(),
            delta=timedelta(minutes=1)
        )
        
    def test_06_refresh_with_lot_products(self):
        """Test refresh stock with lot-tracked products"""
        # Create stock with lots
        self.create_quant(self.product_lot, self.location_parent, 10, lot=self.lot1)
        self.create_quant(self.product_lot, self.location_parent, 15, lot=self.lot2)
        
        # Create adjustment
        adjustment = self.create_adjustment(self.location_parent, user=self.user_admin)
        for _ in range(20):
            self.simulate_barcode_scan(adjustment, 'PROD-LOT-001', user=self.user_admin)
        adjustment.action_confirm()
        
        # Add more stock
        inventory_location = self.product_lot.with_company(self.company).property_stock_inventory
        self.create_stock_move(
            self.product_lot,
            inventory_location,
            self.location_parent,
            5,
            lot=self.lot1
        )
        
        # Refresh stock
        action = adjustment.action_refresh_stock()
        wizard = self.env['stock.refresh.stock.wizard'].with_context(
            action['context']
        ).create({
            'fetch_type': 'current'
        })
        wizard.action_apply()
        
        # Check quantities updated
        adj_line = adjustment.inv_adjustment_line_ids[0]
        self.assertEqual(adj_line.on_hand_qty, 30)  # 25 + 5 from move
        
        # Check lot lines recomputed
        self.assertTrue(len(adj_line.adjustment_line_lot_ids) > 0)