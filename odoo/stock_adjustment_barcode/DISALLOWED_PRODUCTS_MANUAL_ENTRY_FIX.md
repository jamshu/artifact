# Disallowed Products Manual Entry Prevention

## Problem Statement

Previously, while parent products (from BOM transfers) were blocked during barcode scanning, users could still manually select these disallowed products through the product dropdown in the adjustment line info records. This created an inconsistency:

- ❌ **Barcode Scan**: Parent products blocked → Good ✓
- ❌ **Manual Entry**: Parent products selectable → Bad ✗

This allowed users to bypass the BOM transfer consolidation logic by manually adding parent products directly.

## Solution Implemented

Added dynamic domain filtering and validation to prevent manual selection of disallowed products in the adjustment line info records.

### Changes Made

#### 1. Model Changes - `stock_adjustment_barcode_line_info.py`

**Added new field:**
```python
disallowed_product_ids = fields.Many2many(
    comodel_name='product.product',
    compute='_compute_disallowed_product_ids',
    store=False,
    help='Products that are not allowed to be scanned directly (parent products from BOM transfers)'
)
```

**Modified product_id field domain:**
```python
product_id = fields.Many2one(
    comodel_name='product.product',
    string="Product",
    domain="[('type', '=', 'product'), ('id', 'not in', disallowed_product_ids)]",
    required=True,
    check_company=True
)
```

**Added compute method:**
```python
@api.depends('inv_adjustment_id', 'inv_adjustment_id.disallowed_products_json')
def _compute_disallowed_product_ids(self):
    """
    Computes the list of disallowed products from the parent adjustment.
    These are parent products that should not be manually selected.
    """
    for record in self:
        if record.inv_adjustment_id and record.inv_adjustment_id.disallowed_products_json:
            disallowed_ids = record.inv_adjustment_id.disallowed_products_json
            record.disallowed_product_ids = [(6, 0, disallowed_ids)]
        else:
            record.disallowed_product_ids = [(6, 0, [])]
```

**Added validation constraint:**
```python
@api.constrains('product_id')
def _check_disallowed_product(self):
    """
    Validates that the selected product is not in the disallowed products list.
    Prevents manual selection of parent products from BOM transfers.
    """
    for record in self:
        if record.inv_adjustment_id and record.inv_adjustment_id.disallowed_products_json:
            disallowed_ids = record.inv_adjustment_id.disallowed_products_json
            if record.product_id.id in disallowed_ids:
                raise ValidationError(_(
                    f"Product '{record.product_id.name}' is not allowed to be added directly. "
                    f"It should appear as a parent product when scanning its child products."))
```

#### 2. View Changes

**Updated 3 tree views to include disallowed_product_ids:**

1. **stock_adjustment_barcode_line_info_views.xml** (standalone view)
```xml
<tree editable="top" create="0" edit="0" delete="0">
    <field name="inv_adjustment_id" invisible="1"/>
    <field name="disallowed_product_ids" invisible="1"/>
    <field name="product_id"/>
    ...
</tree>
```

2. **stock_adjustment_barcode_views.xml** (scan form inline view, line 18-30)
```xml
<field name="inv_adjustment_line_info_ids" mode="tree">
    <tree editable="bottom">
        <field name="inv_adjustment_id" invisible="1"/>
        <field name="disallowed_product_ids" invisible="1"/>
        <field name="product_id"/>
        ...
    </tree>
</field>
```

3. **stock_adjustment_barcode_views.xml** (main form nested view, line 204-212)
```xml
<field name="adjustment_line_info_ids" mode="tree" readonly="1">
    <tree create="0" edit="0">
        <field name="inv_adjustment_id" invisible="1"/>
        <field name="disallowed_product_ids" invisible="1"/>
        <field name="product_id"/>
        ...
    </tree>
</field>
```

## How It Works

### 1. Domain Filtering (Primary Prevention)

When a user opens the product dropdown to manually add a product:

1. System computes `disallowed_product_ids` from parent adjustment's `disallowed_products_json`
2. Domain filter `('id', 'not in', disallowed_product_ids)` applies automatically
3. Parent products are **not shown** in the dropdown list
4. User can only select allowed child products

**Example:**
```
Available Products Dropdown:
✓ Arjoon Mamool 400 gms - No added Sugar (child)
✓ Arjoon Mamool Cardamom 400 gms (child)
✗ Arjoon Mamool Assorted 400 gms 3 in 1 (parent - HIDDEN)
```

### 2. Validation Constraint (Secondary Prevention)

If somehow a disallowed product gets selected (e.g., through API or manual database entry):

1. `_check_disallowed_product()` constraint triggers on save
2. Validation error raised with clear message
3. Record creation/update is blocked

**Error Message:**
```
Product 'Arjoon Mamool Assorted 400 gms 3 in 1' is not allowed to be added directly. 
It should appear as a parent product when scanning its child products.
```

### 3. Dynamic Computation

The `disallowed_product_ids` field is computed dynamically:
- Depends on `inv_adjustment_id.disallowed_products_json`
- Updates automatically when parent adjustment's disallowed list changes
- No stored data - always reflects current state

## User Experience

### Before Fix
```
User Action: Manually add product via dropdown
System: Shows ALL products including parent products
Result: ❌ User can select "Arjoon Mamool Assorted 400 gms 3 in 1"
Problem: Bypasses BOM consolidation logic
```

### After Fix
```
User Action: Manually add product via dropdown
System: Shows only ALLOWED products (filters out parents)
Result: ✓ User CANNOT select "Arjoon Mamool Assorted 400 gms 3 in 1"
Benefit: Enforces BOM consolidation logic consistently
```

## Complete Protection Strategy

The system now has **3 layers of protection**:

### Layer 1: Barcode Scanning
- `on_barcode_scanned()` checks disallowed products
- Blocks scanning of parent products
- Shows error message

### Layer 2: Domain Filtering (NEW)
- Dynamic domain on `product_id` field
- Hides disallowed products from dropdown
- Prevents selection at UI level

### Layer 3: Validation Constraint (NEW)
- `_check_disallowed_product()` constraint
- Validates on save/create
- Catches any bypass attempts

## Testing Scenarios

### ✅ Test Case 1: Dropdown Filter
1. Create inventory adjustment
2. Scan child product "Arjoon Mamool 400 gms"
3. System auto-initializes disallowed products
4. Try to manually add product via dropdown
5. **Expected**: Parent product not visible in dropdown
6. **Result**: ✓ PASS

### ✅ Test Case 2: Validation Error
1. Create inventory adjustment
2. Add disallowed product ID manually via RPC/API
3. **Expected**: Validation error raised
4. **Result**: ✓ PASS

### ✅ Test Case 3: Child Product Selection
1. Create inventory adjustment
2. Scan child product to initialize disallowed list
3. Try to manually add another child product
4. **Expected**: Child product visible and selectable
5. **Result**: ✓ PASS

### ✅ Test Case 4: Dynamic Update
1. Create inventory adjustment
2. Initially no disallowed products
3. Scan child product (triggers auto-initialization)
4. **Expected**: Domain updates, parent filtered out
5. **Result**: ✓ PASS

## Files Modified

1. **models/stock_adjustment_barcode_line_info.py**
   - Added `disallowed_product_ids` field
   - Modified `product_id` field domain
   - Added `_compute_disallowed_product_ids()` method
   - Added `_check_disallowed_product()` constraint

2. **views/stock_adjustment_barcode_line_info_views.xml**
   - Added invisible `disallowed_product_ids` field to tree view

3. **views/stock_adjustment_barcode_views.xml**
   - Added invisible `disallowed_product_ids` field to scan form inline tree
   - Added invisible `disallowed_product_ids` field to main form nested tree
   - Added invisible `inv_adjustment_id` field to all three locations

## Benefits

✅ **Consistent Enforcement**: Same rules apply for both scanning and manual entry  
✅ **User-Friendly**: Products simply don't appear in dropdown (better than error message)  
✅ **Fail-Safe**: Validation constraint as backup if domain is bypassed  
✅ **Dynamic**: Updates automatically when disallowed products change  
✅ **Clean UI**: Invisible fields don't clutter the interface  
✅ **Maintainable**: Single source of truth (`disallowed_products_json`)  

## Related Features

- **BOM Transfer Consolidation**: `/addons-mrp/mrp_bom_transfer_auto`
- **Auto-Initialize Disallowed Products**: `_auto_initialize_disallowed_products()`
- **Barcode Scanning Protection**: `on_barcode_scanned()`
- **Parent-Child Display**: `display_name_with_relation` field
- **BOM Quantity Conversion**: `_compute_parent_qty_from_children()`

## Configuration

No configuration needed. The system automatically:
1. Detects BOM transfers when child products are scanned
2. Populates `disallowed_products_json` with parent products
3. Applies domain filtering to all line info views
4. Validates on save to prevent bypasses

Works seamlessly with existing BOM transfer setup.
