#!/usr/bin/env python3
"""
Test script to verify the net quantity calculation logic for Create Bill from Receipts
This demonstrates the three scenarios:
1. All positive quantities -> Create vendor bill
2. All negative quantities -> Create credit note  
3. Mixed quantities -> Raise error
"""

from collections import defaultdict


def simulate_net_quantity_calculation(moves_data):
    """
    Simulates the net quantity calculation logic.
    
    Args:
        moves_data: List of tuples (product_name, location_usage, location_dest_usage, qty_done)
    
    Returns:
        Dictionary with product quantities and scenario analysis
    """
    product_dict = defaultdict(lambda: 0)
    
    for product_name, location_usage, location_dest_usage, qty_done in moves_data:
        # Receipts: from supplier/external to internal location (positive quantity)
        if location_dest_usage == 'internal' and location_usage != 'internal':
            product_dict[product_name] += qty_done
            print(f"  Receipt: {product_name} +{qty_done} (supplier -> internal)")
        # Returns: from internal to supplier/external location (negative quantity)
        elif location_usage == 'internal' and location_dest_usage != 'internal':
            product_dict[product_name] -= qty_done
            print(f"  Return:  {product_name} -{qty_done} (internal -> supplier)")
    
    # Check if all quantities are positive, negative, or mixed
    has_positive = False
    has_negative = False
    has_zero = False
    
    for product_name, net_qty in product_dict.items():
        if net_qty == 0:
            has_zero = True
        elif net_qty > 0:
            has_positive = True
        else:  # net_qty < 0
            has_negative = True
    
    # Determine the scenario
    if has_positive and has_negative:
        scenario = "ERROR: Mixed quantities"
        move_type = None
        action = "Raise error - Cannot create bill with mixed positive and negative quantities"
    elif has_negative and not has_positive:
        scenario = "All negative quantities"
        move_type = "in_refund"
        action = "Create vendor credit note"
    else:
        scenario = "All positive quantities (or all zero)"
        move_type = "in_invoice"
        action = "Create vendor bill"
    
    return {
        'product_quantities': dict(product_dict),
        'has_positive': has_positive,
        'has_negative': has_negative,
        'has_zero': has_zero,
        'scenario': scenario,
        'move_type': move_type,
        'action': action
    }


def print_scenario_result(scenario_name, moves_data):
    """Print the results of a scenario test."""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {scenario_name}")
    print('='*60)
    print("\nMoves:")
    
    result = simulate_net_quantity_calculation(moves_data)
    
    print("\nNet Quantities by Product:")
    for product, qty in result['product_quantities'].items():
        status = "✓ Positive" if qty > 0 else ("✗ Negative" if qty < 0 else "○ Zero")
        print(f"  {product}: {qty:+.2f} [{status}]")
    
    print(f"\nAnalysis:")
    print(f"  Has positive quantities: {result['has_positive']}")
    print(f"  Has negative quantities: {result['has_negative']}")
    print(f"  Has zero quantities: {result['has_zero']}")
    
    print(f"\nResult:")
    print(f"  Scenario: {result['scenario']}")
    print(f"  Move Type: {result['move_type']}")
    print(f"  Action: {result['action']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("NET QUANTITY CALCULATION TEST FOR CREATE BILL FROM RECEIPTS")
    print("="*60)
    
    # Scenario 1: Only receipts (all positive)
    scenario1_moves = [
        ("Product A", "supplier", "internal", 10),
        ("Product B", "supplier", "internal", 5),
        ("Product C", "supplier", "internal", 20),
    ]
    print_scenario_result("Only Receipts (All Positive)", scenario1_moves)
    
    # Scenario 2: Only returns (all negative)
    scenario2_moves = [
        ("Product A", "internal", "supplier", 3),
        ("Product B", "internal", "supplier", 2),
        ("Product C", "internal", "supplier", 5),
    ]
    print_scenario_result("Only Returns (All Negative)", scenario2_moves)
    
    # Scenario 3: Mixed - some products net positive, others net negative (ERROR)
    scenario3_moves = [
        # Product A: 10 received, 3 returned = +7 (positive)
        ("Product A", "supplier", "internal", 10),
        ("Product A", "internal", "supplier", 3),
        # Product B: 5 received, 8 returned = -3 (negative)
        ("Product B", "supplier", "internal", 5),
        ("Product B", "internal", "supplier", 8),
        # Product C: 20 received, 5 returned = +15 (positive)
        ("Product C", "supplier", "internal", 20),
        ("Product C", "internal", "supplier", 5),
    ]
    print_scenario_result("Mixed Positive and Negative (ERROR)", scenario3_moves)
    
    # Scenario 4: Net positive for all products (receipts > returns)
    scenario4_moves = [
        # Product A: 10 received, 3 returned = +7
        ("Product A", "supplier", "internal", 10),
        ("Product A", "internal", "supplier", 3),
        # Product B: 8 received, 2 returned = +6
        ("Product B", "supplier", "internal", 8),
        ("Product B", "internal", "supplier", 2),
        # Product C: 20 received, 5 returned = +15
        ("Product C", "supplier", "internal", 20),
        ("Product C", "internal", "supplier", 5),
    ]
    print_scenario_result("Net Positive for All Products", scenario4_moves)
    
    # Scenario 5: Net negative for all products (returns > receipts)
    scenario5_moves = [
        # Product A: 3 received, 10 returned = -7
        ("Product A", "supplier", "internal", 3),
        ("Product A", "internal", "supplier", 10),
        # Product B: 2 received, 8 returned = -6
        ("Product B", "supplier", "internal", 2),
        ("Product B", "internal", "supplier", 8),
        # Product C: 5 received, 20 returned = -15
        ("Product C", "supplier", "internal", 5),
        ("Product C", "internal", "supplier", 20),
    ]
    print_scenario_result("Net Negative for All Products", scenario5_moves)
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)
