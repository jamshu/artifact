#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify that parent line info copying works correctly.
This script simulates the BOM consolidation process and checks that
line info records are correctly linked to parent lines.
"""

import sys
import os

# Add Odoo to path
sys.path.insert(0, '/Users/jamshid/PycharmProjects/Siafa/src')

from odoo import api, SUPERUSER_ID
from odoo.cli import server

def test_parent_line_info_copy(env):
    """Test that line info is correctly copied to parent lines"""
    
    print("=" * 80)
    print("Testing Parent Line Info Copy Fix")
    print("=" * 80)
    
    # Find a stock adjustment in draft state
    adjustment_model = env['stock.adjustment.barcode']
    adjustments = adjustment_model.search([('state', '=', 'draft')], limit=1)
    
    if not adjustments:
        print("No draft adjustments found. Please create one first.")
        return False
    
    adjustment = adjustments[0]
    print(f"Using adjustment: {adjustment.name} (ID: {adjustment.id})")
    
    # Check for parent-child relationships after consolidation
    parent_lines = adjustment.inv_adjustment_line_ids.filtered(
        lambda l: l.is_parent_line
    )
    
    print(f"\nFound {len(parent_lines)} parent lines")
    
    success = True
    for parent_line in parent_lines:
        print(f"\n--- Parent Line: {parent_line.product_id.name} (ID: {parent_line.id}) ---")
        
        # Get child lines
        child_lines = adjustment.inv_adjustment_line_ids.filtered(
            lambda l: l.parent_product_id == parent_line.product_id
        )
        print(f"  Child lines: {len(child_lines)}")
        
        # Check parent line info
        parent_info = parent_line.adjustment_line_info_ids
        print(f"  Parent line info records: {len(parent_info)}")
        
        # Verify each parent info record
        for info in parent_info:
            if info.inv_adjustment_line_id.id != parent_line.id:
                print(f"  ❌ ERROR: Line info {info.id} has wrong line_id!")
                print(f"     Expected: {parent_line.id}, Got: {info.inv_adjustment_line_id.id}")
                success = False
            else:
                print(f"  ✓ Line info {info.id}: Product={info.product_id.name}, "
                      f"Qty={info.scanned_qty}, User={info.scanned_user_id.name}, "
                      f"Line ID={info.inv_adjustment_line_id.id}")
        
        # Check child line info (should still exist)
        for child_line in child_lines:
            child_info = child_line.adjustment_line_info_ids
            print(f"\n  Child Line: {child_line.product_id.name} (ID: {child_line.id})")
            print(f"    Child line info records: {len(child_info)}")
            for info in child_info:
                if info.inv_adjustment_line_id.id != child_line.id:
                    print(f"    ❌ ERROR: Child info {info.id} has wrong line_id!")
                    print(f"       Expected: {child_line.id}, Got: {info.inv_adjustment_line_id.id}")
                    success = False
                else:
                    print(f"    ✓ Info: Qty={info.scanned_qty}, Line ID={info.inv_adjustment_line_id.id}")
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED: All line info records correctly linked!")
    else:
        print("❌ TEST FAILED: Some line info records have incorrect line_id!")
    print("=" * 80)
    
    return success


def main():
    """Main test function"""
    # Initialize Odoo
    server.main(['-c', '/Users/jamshid/PycharmProjects/Siafa/src/odoo.conf', '--stop-after-init', '--no-http'])
    
    # Get environment
    with api.Environment.manage():
        registry = odoo.registry('odoo16e_simc')
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            test_parent_line_info_copy(env)


if __name__ == '__main__':
    import odoo
    main()