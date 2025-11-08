# Parent Line Info Copy - Audit Trail Enhancement

## Problem Statement

Previously, when child products were scanned and consolidated to a parent product:
- ✅ Child lines kept their own scanned line info records
- ✅ Parent line calculated quantities from children
- ❌ **Parent line had NO scanned line info records**

This meant users had to:
1. Find child lines to see who scanned what
2. Navigate between parent and multiple child lines
3. Manually piece together the audit trail

**Example Problem:**
```
Parent Line: Arjoon Mamool Assorted 400 gms 3 in 1 (24 units)
├─ Line Info: EMPTY ❌
└─ No visibility of scans from parent view

Child Line 1: Arjoon Mamool 400 gms - No added Sugar (5 units)
├─ Line Info: User A scanned 3 units
└─ Line Info: User B scanned 2 units

Child Line 2: Arjoon Mamool Cardamom 400 gms (3 units)  
└─ Line Info: User A scanned 3 units
```

Users couldn't see from the parent line that:
- User A scanned products
- User B scanned products
- Which specific child products were scanned

## Solution Implemented

Added functionality to **copy** child scanned line info records to the parent line during BOM consolidation, while **keeping** the original records on child lines.

### Key Features

1. **Copies Line Info to Parent**: All child scanned records copied to parent
2. **Preserves Child Records**: Original child line info remains intact
3. **Duplicate Prevention**: Checks to avoid creating duplicates
4. **Cleanup on Reset**: Removes copied records when resetting to draft
5. **Full Audit Trail**: Complete scan history visible from parent

## How It Works

### During Consolidation (On Confirm)

When `action_confirm()` is called:

1. **BOM Consolidation Runs**
   ```python
   _handle_bom_transfer_consolidation()
   ```

2. **For Each Parent-Child Group**:
   - Create or find parent line
   - Call `_copy_child_line_info_to_parent(parent_line, child_lines)`

3. **Copy Process**:
   ```python
   # Collect all child line info
   for child_line in child_lines:
       all_child_line_info |= child_line.adjustment_line_info_ids
   
   # Create copies for parent
   for child_info in all_child_line_info:
       # Create duplicate on parent line
       line_info_obj.create({
           'product_id': child_info.product_id.id,
           'scanned_qty': child_info.scanned_qty,
           'scanned_user_id': child_info.scanned_user_id.id,
           'inv_adjustment_line_id': parent_line.id,  # Link to parent!
           ...
       })
   ```

4. **Duplicate Prevention**:
   - Checks if exact same record exists on parent
   - Matches: product, quantity, user, lot
   - Skips if already copied

### Data Structure After Consolidation

```
Parent Line: Arjoon Mamool Assorted 400 gms 3 in 1 (24 units)
├─ Line Info: User A scanned 3 units [Arjoon Mamool 400 gms] ✓ COPY
├─ Line Info: User B scanned 2 units [Arjoon Mamool 400 gms] ✓ COPY
└─ Line Info: User A scanned 3 units [Arjoon Mamool Cardamom] ✓ COPY

Child Line 1: Arjoon Mamool 400 gms - No added Sugar (5 units)
├─ Line Info: User A scanned 3 units ✓ ORIGINAL
└─ Line Info: User B scanned 2 units ✓ ORIGINAL

Child Line 2: Arjoon Mamool Cardamom 400 gms (3 units)  
└─ Line Info: User A scanned 3 units ✓ ORIGINAL
```

### During Cleanup (On Reset/Cancel)

When `action_cancel()` or `action_reset_to_draft()` is called:

1. **Cleanup Process**:
   ```python
   _cleanup_bom_transfer_consolidation()
   ```

2. **Remove Copied Records**:
   ```python
   # Find parent line info that are copies (product_id != parent product)
   parent_info_to_remove = parent_line.adjustment_line_info_ids.filtered(
       lambda info: info.product_id != parent_line.product_id
   )
   parent_info_to_remove.unlink()
   ```

3. **Preserve Child Records**:
   - Child line info records are NOT touched
   - Only parent copies are removed

4. **Remove Auto-Created Parents**:
   - If parent line has no line info after cleanup → delete parent line
   - This handles auto-created parent lines

## Code Changes

### File: `models/stock_adjustment_barcode.py`

#### 1. New Method: `_copy_child_line_info_to_parent()`

**Location**: Lines 225-263

**Purpose**: Copy child scanned line info records to parent line

**Key Features**:
- Collects all child line info records
- Creates duplicate records linked to parent line
- Prevents duplicates with existence check
- Maintains all original metadata (user, qty, lot, UoM)

**Code**:
```python
def _copy_child_line_info_to_parent(self, parent_line, child_lines):
    """
    Copy child scanned line info records to parent line.
    This creates duplicate info records on the parent so all related scans
    can be viewed from the parent line itself.
    """
    line_info_obj = self.env['stock.adjustment.barcode.line.info']
    
    # Collect all child line info records
    all_child_line_info = self.env['stock.adjustment.barcode.line.info']
    for child_line in child_lines:
        all_child_line_info |= child_line.adjustment_line_info_ids
    
    # Create copies of each child line info record for the parent
    for child_info in all_child_line_info:
        # Check if already exists (avoid duplicates)
        existing = parent_line.adjustment_line_info_ids.filtered(
            lambda i: i.product_id == child_info.product_id and 
                     i.scanned_qty == child_info.scanned_qty and 
                     i.scanned_user_id == child_info.scanned_user_id and
                     i.lot_id == child_info.lot_id
        )
        
        if not existing:
            # Create copy for parent
            line_info_obj.create({
                'product_id': child_info.product_id.id,
                'lot_id': child_info.lot_id.id if child_info.lot_id else False,
                'product_uom_id': child_info.product_uom_id.id,
                'scanned_qty': child_info.scanned_qty,
                'scanned_user_id': child_info.scanned_user_id.id,
                'inv_adjustment_id': self.id,
                'inv_adjustment_line_id': parent_line.id,  # Link to parent!
            })
```

#### 2. Modified Method: `_handle_bom_transfer_consolidation()`

**Location**: Lines 154-223

**Changes**:
- Added call to `_copy_child_line_info_to_parent()` after parent line creation
- Added comment explaining parent now has copies

**Added Code**:
```python
# Copy child scanned line info records to parent line
# This allows viewing all related scans from the parent
self._copy_child_line_info_to_parent(parent_line, child_lines_recordset)
```

#### 3. Enhanced Method: `_cleanup_bom_transfer_consolidation()`

**Location**: Lines 392-437

**Changes**:
- Added logic to remove copied line info from parent lines
- Identifies copied records by checking product_id mismatch
- Preserves original child line info records
- Only removes auto-created parent lines

**Enhanced Logic**:
```python
# Remove copied line info records from parent lines
for parent_line in parent_lines:
    # Remove parent line info that are copies from children
    # (product_id of info != product_id of parent line)
    parent_info_to_remove = parent_line.adjustment_line_info_ids.filtered(
        lambda info: info.product_id != parent_line.product_id
    )
    parent_info_to_remove.unlink()
```

## User Experience

### Before Enhancement

**Viewing Parent Line:**
```
Parent Line: Arjoon Mamool Assorted 400 gms 3 in 1
Total Scanned Qty: 24 units
Line Info Records: 0 ❌

User must navigate to each child line to see scan details
```

**Audit Trail:** Fragmented across multiple child lines

### After Enhancement

**Viewing Parent Line:**
```
Parent Line: Arjoon Mamool Assorted 400 gms 3 in 1
Total Scanned Qty: 24 units
Line Info Records: ✅

Scanned Line Details:
├─ Arjoon Mamool 400 gms - No added Sugar | 3 units | User A
├─ Arjoon Mamool 400 gms - No added Sugar | 2 units | User B
└─ Arjoon Mamool Cardamom 400 gms | 3 units | User A
```

**Audit Trail:** Complete and visible from parent line!

### Benefits for Users

✅ **Complete Visibility**: See all scans from parent line  
✅ **No Navigation**: Don't need to check each child line  
✅ **Audit Trail**: Full history of who scanned what  
✅ **Product Details**: Know which child products were scanned  
✅ **User Tracking**: See which users performed scans  
✅ **Quantity Breakdown**: Detailed scan quantities per user  

## Example Scenarios

### Scenario 1: Multiple Users Scanning Different Products

**Scanning Phase:**
- User A scans 3x "Arjoon Mamool 400 gms - No added Sugar"
- User B scans 2x "Arjoon Mamool 400 gms - No added Sugar"
- User A scans 3x "Arjoon Mamool Cardamom 400 gms"

**After Consolidation:**
```
Parent: Arjoon Mamool Assorted 400 gms 3 in 1 (24 units total)
View "Scanned Line" tab:
  ├─ Product: Arjoon Mamool 400 gms - No added Sugar | Qty: 3 | User: User A
  ├─ Product: Arjoon Mamool 400 gms - No added Sugar | Qty: 2 | User: User B
  └─ Product: Arjoon Mamool Cardamom 400 gms | Qty: 3 | User: User A
```

### Scenario 2: Reset to Draft

**Action:** User clicks "Cancel" then "Reset to Draft"

**System Behavior:**
1. Removes copied line info from parent line
2. Keeps original line info on child lines
3. Removes parent line if it was auto-created
4. Resets parent_product_id on child lines
5. Clears disallowed products list

**Result:**
- Child lines retain their original scan data
- Parent line removed or has no copied data
- System ready for re-scanning

### Scenario 3: Re-Consolidation

**Action:** User confirms adjustment multiple times (testing/corrections)

**System Behavior:**
- Duplicate prevention checks existing parent line info
- Skips creating duplicate copies
- Only adds new scans that weren't previously copied

**Result:** No duplicate line info records on parent

## Technical Details

### Record Linkage

Each copied line info record maintains:
- `inv_adjustment_line_id`: Links to **parent** line
- `product_id`: Original **child** product
- `scanned_user_id`: Original scanning user
- `scanned_qty`: Original scanned quantity
- `lot_id`: Original lot/serial number (if any)

### Identification of Copies

Copied records are identified by:
```python
info.product_id != parent_line.product_id
```

If line info has a different product_id than its parent line, it's a copy from a child.

### Data Integrity

- ✅ Original child records preserved
- ✅ Parent records are true copies
- ✅ All metadata maintained
- ✅ Duplicate prevention
- ✅ Clean cleanup process

## Testing Scenarios

### ✅ Test Case 1: Basic Copy
1. Scan 2 child products
2. Confirm adjustment
3. **Expected**: Parent line shows all child scan records
4. **Expected**: Child lines still have original records

### ✅ Test Case 2: Multiple Users
1. User A scans child product 1
2. User B scans child product 2
3. Confirm adjustment
4. **Expected**: Parent shows both users' scans

### ✅ Test Case 3: Reset to Draft
1. Scan and confirm
2. Cancel adjustment
3. Reset to draft
4. **Expected**: Parent copies removed
5. **Expected**: Child originals preserved

### ✅ Test Case 4: Re-Consolidation
1. Scan and confirm
2. Reset to draft
3. Scan more products
4. Confirm again
5. **Expected**: No duplicate copies on parent

### ✅ Test Case 5: With Lots
1. Scan products with lot/serial numbers
2. Confirm adjustment
3. **Expected**: Lot info preserved in copies

## Related Features

- **BOM Transfer Consolidation**: `/addons-mrp/mrp_bom_transfer_auto`
- **Parent Quantity Conversion**: `_compute_parent_qty_from_children()`
- **Disallowed Products**: Auto-initialization and blocking
- **Parent-Child Display**: Visual indicators in tree view
- **Cleanup on Reset**: `_cleanup_bom_transfer_consolidation()`

## Configuration

No configuration needed. The system automatically:
1. Detects parent-child relationships from BOM transfers
2. Copies child line info to parent during consolidation
3. Prevents duplicate copies
4. Cleans up copies when resetting

Works seamlessly with existing BOM transfer setup.

## Performance Considerations

- **Minimal Overhead**: Only copies records during confirmation
- **No Background Jobs**: Synchronous operation during confirm
- **Efficient Cleanup**: Uses filtered operations for deletion
- **Duplicate Check**: Quick existence check before creation

For typical use cases (dozens of scans), performance impact is negligible.
