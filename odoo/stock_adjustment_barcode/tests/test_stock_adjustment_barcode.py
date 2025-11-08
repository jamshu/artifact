# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import datetime


class TestStockAdjustmentBarcode(TransactionCase):
    """Test cases for stock adjustment barcode functionality"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Use existing company instead of creating a new one
        cls.company = cls.env.company
        
        # Try to find existing warehouse or use first one
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.company.id)], limit=1)
        if not cls.warehouse:
            # Create partner for warehouse
            partner = cls.env['res.partner'].create({
                'name': 'Test Warehouse Partner',
                'company_id': cls.company.id,
            })
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Test Warehouse',
                'code': 'TWH',
                'partner_id': partner.id,
                'company_id': cls.company.id,
            })
        
        cls.stock_location = cls.env['stock.location'].create({
            'name': 'Test Stock Location',
            'usage': 'internal',
            'warehouse_id': cls.warehouse.id,
            'company_id': cls.company.id,
        })
        
        # Create test products
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Test Product 1',
            'type': 'product',
            'categ_id': cls.env.ref('product.product_category_all').id,
            'list_price': 100.0,
            'standard_price': 50.0,
        })
        
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Test Product 2',
            'type': 'product',
            'categ_id': cls.env.ref('product.product_category_all').id,
            'list_price': 200.0,
            'standard_price': 100.0,
        })
        
        # Use existing admin user
        cls.test_user = cls.env.ref('base.user_admin')
        
        # Create stock quants
        cls.env['stock.quant'].create({
            'product_id': cls.product_1.id,
            'location_id': cls.stock_location.id,
            'quantity': 10.0,
            'company_id': cls.company.id,
        })
        
        cls.env['stock.quant'].create({
            'product_id': cls.product_2.id,
            'location_id': cls.stock_location.id,
            'quantity': 20.0,
            'company_id': cls.company.id,
        })

    def test_01_create_adjustment(self):
        """Test creating a stock adjustment"""
        adjustment = self.env['stock.adjustment.barcode'].create({
            'name': 'TEST/ADJ/001',
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
        })
        
        self.assertEqual(adjustment.state, 'draft')
        self.assertEqual(adjustment.location_id, self.stock_location)
        self.assertEqual(adjustment.company_id, self.company)
        self.assertFalse(adjustment.inv_adjustment_line_ids)

    def test_02_add_line_info(self):
        """Test adding line info to an adjustment"""
        adjustment = self.env['stock.adjustment.barcode'].create({
            'name': 'TEST/ADJ/002',
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
        })
        
        # Add scanned line info
        line_info = self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_1.id,
            'scanned_qty': 5.0,
            'scanned_user_id': self.test_user.id,
        })
        
        self.assertEqual(line_info.inv_adjustment_id, adjustment)
        self.assertEqual(line_info.scanned_qty, 5.0)
        
        # Check that adjustment line was created
        self.assertTrue(adjustment.inv_adjustment_line_ids)
        self.assertEqual(len(adjustment.inv_adjustment_line_ids), 1)
        
        line = adjustment.inv_adjustment_line_ids[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.total_scanned_qty, 5.0)

    def test_03_confirm_adjustment(self):
        """Test confirming a stock adjustment"""
        adjustment = self.env['stock.adjustment.barcode'].create({
            'name': 'TEST/ADJ/003',
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
        })
        
        # Add line info
        self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_1.id,
            'scanned_qty': 8.0,
            'scanned_user_id': self.test_user.id,
        })
        
        # Confirm adjustment
        adjustment.action_confirm()
        
        self.assertEqual(adjustment.state, 'to_approve')
        self.assertTrue(adjustment.inv_adjustment_line_ids)

    def test_04_approve_adjustment(self):
        """Test approving a stock adjustment"""
        adjustment = self.env['stock.adjustment.barcode'].create({
            'name': 'TEST/ADJ/004',
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
        })
        
        # Add line info
        self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_1.id,
            'scanned_qty': 8.0,
            'scanned_user_id': self.test_user.id,
        })
        
        # Confirm and approve
        adjustment.action_confirm()
        adjustment.action_approved()
        
        self.assertEqual(adjustment.state, 'approved')
        self.assertEqual(adjustment.approved_by, self.env.user)

    def test_05_cancel_adjustment(self):
        """Test cancelling a stock adjustment"""
        adjustment = self.env['stock.adjustment.barcode'].create({
            'name': 'TEST/ADJ/005',
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
        })
        
        # Add line info
        self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_1.id,
            'scanned_qty': 8.0,
            'scanned_user_id': self.test_user.id,
        })
        
        # Confirm and then cancel
        adjustment.action_confirm()
        adjustment.action_cancel()
        
        self.assertEqual(adjustment.state, 'cancel')  # Fixed: state is 'cancel' not 'cancelled'

    def test_06_reset_to_draft(self):
        """Test resetting adjustment to draft"""
        adjustment = self.env['stock.adjustment.barcode'].create({
            'name': 'TEST/ADJ/006',
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
        })
        
        # Add line info
        self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_1.id,
            'scanned_qty': 8.0,
            'scanned_user_id': self.test_user.id,
        })
        
        # Confirm, cancel, then reset
        adjustment.action_confirm()
        adjustment.action_cancel()
        adjustment.action_reset_to_draft()
        
        self.assertEqual(adjustment.state, 'draft')

    def test_07_multiple_scans_same_product(self):
        """Test multiple scans of the same product"""
        adjustment = self.env['stock.adjustment.barcode'].create({
            'name': 'TEST/ADJ/007',
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
        })
        
        # Add multiple scans
        self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_1.id,
            'scanned_qty': 3.0,
            'scanned_user_id': self.test_user.id,
        })
        
        self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_1.id,
            'scanned_qty': 2.0,
            'scanned_user_id': self.test_user.id,
        })
        
        # Should have one line with combined quantity
        self.assertEqual(len(adjustment.inv_adjustment_line_ids), 1)
        line = adjustment.inv_adjustment_line_ids[0]
        self.assertEqual(line.total_scanned_qty, 5.0)
        self.assertEqual(len(line.adjustment_line_info_ids), 2)

    def test_08_disallowed_products(self):
        """Test disallowed products functionality"""
        adjustment = self.env['stock.adjustment.barcode'].create({
            'name': 'TEST/ADJ/008',
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
            'disallowed_products_json': [self.product_1.id],
        })
        
        self.assertIn(self.product_1.id, adjustment.disallowed_products_json)
        
        # Create line info to check disallowed products
        line_info = self.env['stock.adjustment.barcode.line.info'].create({
            'inv_adjustment_id': adjustment.id,
            'product_id': self.product_2.id,  # Use allowed product
            'scanned_qty': 5.0,
            'scanned_user_id': self.test_user.id,
        })
        
        # Check that disallowed products are computed correctly
        self.assertIn(self.product_1.id, [p.id for p in line_info.disallowed_product_ids])