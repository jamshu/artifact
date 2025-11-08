# BOM Conversion Fix for Stock Adjustment Barcode

## Problem Statement

When scanning child products during inventory adjustment, the system was incorrectly calculating the parent product quantity by directly summing the child quantities without considering the BOM (Bill of Materials) conversion ratios.

### Previous Incorrect Behavior
```python
# Line 240 (OLD CODE - INCORRECT)
total_scanned_qty = sum(child_lines.mapped('total_scanned_qty'))
```

This simply added up child quantities without considering:
- BOM conversion ratios (e.g., 1 child unit = 3 parent units)
- Different units of measure (e.g., grams vs units)

## Solution Implemented

### New Conversion Logic

Added a new method `_compute_parent_qty_from_children()` that:
1. Retrieves the BOM for each child product
2. Calculates the conversion ratio from the BOM structure
3. Handles UoM (Unit of Measure) conversions
4. Sums the converted quantities to get the correct parent quantity

### BOM Structure

```
mrp.bom (type='transfer'):
├── product_tmpl_id: Child Product (e.g., "Arjoon Mamool 400 gms - No added Sugar")
├── product_qty: Child quantity in BOM (e.g., 1.0 unit)
└── bom_line_ids:
    ├── product_id: Parent Product (e.g., "Arjoon Mamool Assorted 400 gms 3 in 1")
    ├── product_qty: Parent quantity produced (e.g., 3.0 units)
    └── product_uom_id: Unit of measure
```

### Conversion Formula

```
Parent Quantity = (Scanned Child Qty / BOM Child Qty) × BOM Parent Qty
```

## Examples

### Example 1: Simple Unit Conversion
**Scenario:**
- Child Product: "Arjoon Mamool 400 gms - No added Sugar"
- Scanned: 5 units
- BOM Setup: 1 child unit → 3 parent units

**Calculation:**
```
Parent Qty = (5 / 1) × 3 = 15 units
```

### Example 2: Multiple Children to One Parent
**Scenario:**
- Child 1: "Arjoon Mamool 400 gms - No added Sugar" - scanned 5 units
- Child 2: "Arjoon Mamool Cardamom 400 gms" - scanned 3 units
- Both have BOM: 1 child unit → 3 parent units

**Calculation:**
```
Child 1: (5 / 1) × 3 = 15 parent units
Child 2: (3 / 1) × 3 = 9 parent units
Total Parent Qty = 15 + 9 = 24 units
```

### Example 3: Weight to Unit Conversion
**Scenario:**
- Child Product measured in grams
- Scanned: 400 grams
- BOM Setup: 400 grams → 1 parent unit

**Calculation:**
```
Parent Qty = (400 / 400) × 1 = 1 unit
```

### Example 4: Different Ratio
**Scenario:**
- Scanned: 10 units
- BOM Setup: 2 child units → 5 parent units

**Calculation:**
```
Parent Qty = (10 / 2) × 5 = 25 parent units
```

## Code Changes

### File Modified
`addons-stock/stock_adjustment_barcode/models/stock_adjustment_barcode_line.py`

### Changes Made

1. **Added new method** `_get_bom_transfer_for_child()` (Line 214-239)
   - Returns the BOM record for a child product
   - Handles warehouse filtering

2. **Added new method** `_compute_parent_qty_from_children()` (Line 241-330)
   - Computes parent quantity from child lines using BOM ratios
   - Handles UoM conversions
   - Includes detailed documentation

3. **Modified** `_compute_product_qty()` (Line 337)
   - Changed from direct sum to BOM-based conversion
   - Old: `total_scanned_qty = sum(child_lines.mapped('total_scanned_qty'))`
   - New: `total_scanned_qty = record._compute_parent_qty_from_children(child_lines)`

## How It Works

### Scanning Phase
1. User scans child products (e.g., "Arjoon Mamool 400 gms - No added Sugar")
2. System creates adjustment line info records for each scanned product
3. Each child line tracks its own scanned quantities

### Consolidation Phase (On Confirm)
1. System detects products with BOM transfer relationships
2. Creates parent line for consolidated product
3. Marks child lines with `parent_product_id`
4. Child lines keep their adjustment_line_info_ids for audit trail

### Quantity Calculation
1. Child lines show their own scanned quantities
2. Parent line automatically calculates `total_scanned_qty` by:
   - Getting all child lines with matching `parent_product_id`
   - For each child line:
     - Retrieving its BOM transfer
     - Extracting conversion ratios
     - Converting child qty to parent qty
     - Handling UoM conversions
   - Summing all converted quantities

### Stock Move Creation
1. Only parent lines create stock moves
2. Child lines are filtered out (due to `is_child_line` flag)
3. Parent's stock move uses the converted quantity

## Benefits

✅ **Accurate Inventory**: Parent quantities correctly reflect BOM ratios  
✅ **UoM Support**: Handles different units (grams, units, kg, etc.)  
✅ **Multi-Child**: Supports multiple child products consolidating to one parent  
✅ **Audit Trail**: Child lines preserved with original scanned quantities  
✅ **Flexible**: Works with any BOM ratio configuration  

## Testing

Test cases validated:
- ✅ Simple 1:3 ratio conversion
- ✅ Complex 2:5 ratio conversion
- ✅ Weight to unit conversion (400g → 1 unit)
- ✅ Multiple children consolidation
- ✅ UoM conversion handling

## Related Modules

- **MRP BOM Transfer Auto**: `/addons-mrp/mrp_bom_transfer_auto`
  - Defines the `transfer` BOM type
  - Handles warehouse filtering
  - Manages COGS adjustment options

- **Stock Adjustment Barcode**: `/addons-stock/stock_adjustment_barcode`
  - Main module for barcode-based inventory adjustments
  - Handles parent-child consolidation
  - Creates stock moves

## Configuration Notes

For proper operation, ensure:
1. BOM type is set to `transfer` in mrp.bom
2. Child product is set as `product_tmpl_id` in BOM
3. Parent product is in `bom_line_ids` with correct `product_qty`
4. UoM categories are consistent (or use same UoM category for conversions)
5. Warehouse filtering is properly configured if needed
