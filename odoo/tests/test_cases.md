# Stock Adjustment Barcode Module - Test Cases

## Test Suite Overview
This document outlines comprehensive test cases for the Stock Adjustment Barcode module in Odoo 16.

## 1. Barcode Scanning Tests

### Test Case 1.1: Product Barcode Scanning
**Objective:** Verify that products can be scanned via barcode
- **Preconditions:** 
  - Product exists with barcode
  - Stock adjustment in draft state
- **Steps:**
  1. Create stock adjustment for location
  2. Scan product barcode
  3. Verify line creation
- **Expected Result:** Product line created with quantity 1

### Test Case 1.2: Multiple Scans Same Product
**Objective:** Verify quantity increments on multiple scans
- **Steps:**
  1. Scan same product barcode twice
  2. Check scanned quantity
- **Expected Result:** Quantity increases to 2

### Test Case 1.3: User Recording
**Objective:** Verify scanned user is recorded
- **Steps:**
  1. User A scans product
  2. User B scans same product
  3. Check line info records
- **Expected Result:** Separate line info records for each user

### Test Case 1.4: User Visibility
**Objective:** Verify users only see their own scans
- **Steps:**
  1. User A scans products
  2. User B logs in and views adjustment
- **Expected Result:** User B sees only their own scans in line info

### Test Case 1.5: Invalid Barcode
**Objective:** Verify error on invalid barcode
- **Steps:**
  1. Scan non-existent barcode
- **Expected Result:** Error message displayed

### Test Case 1.6: Scan in Non-Draft State
**Objective:** Verify scanning blocked in non-draft states
- **Steps:**
  1. Confirm adjustment
  2. Try to scan barcode
- **Expected Result:** Validation error

## 2. Negative Stock Handling Tests

### Test Case 2.1: Zero Negative Stock
**Objective:** Verify negative stock becomes zero
- **Preconditions:**
  - Product with -5 quantity in location
- **Steps:**
  1. Scan product 10 times
  2. Confirm adjustment
  3. Post adjustment
- **Expected Result:** 
  - Negative stock first becomes 0
  - Final quantity is 10

### Test Case 2.2: Multiple Negative Quants
**Objective:** Verify all negative quants handled
- **Preconditions:**
  - Multiple lots with negative quantities
- **Steps:**
  1. Scan total positive quantity
  2. Confirm and post
- **Expected Result:** All negative quants become zero first

## 3. Auto Lot Selection Tests (FIFO)

### Test Case 3.1: FIFO Selection - Stock Addition
**Objective:** Verify first lot selected for additions
- **Preconditions:**
  - Product with multiple lots (LOT001, LOT002, LOT003)
- **Steps:**
  1. Scan product to add stock
  2. Confirm adjustment
- **Expected Result:** Stock added to LOT001 (first lot)

### Test Case 3.2: FIFO Selection - Stock Deduction
**Objective:** Verify FIFO deduction across lots
- **Preconditions:**
  - LOT001: 10 units
  - LOT002: 15 units
  - LOT003: 5 units
- **Steps:**
  1. Scan to reduce by 20 units
  2. Confirm adjustment
- **Expected Result:**
  - LOT001: 0 units (reduced by 10)
  - LOT002: 5 units (reduced by 10)
  - LOT003: 5 units (unchanged)

### Test Case 3.3: Lot Search in Location
**Objective:** Verify lot search hierarchy
- **Steps:**
  1. Create adjustment for location without lot
  2. System searches in company
- **Expected Result:** Lot found in company if not in location

### Test Case 3.4: No Quants Available
**Objective:** Verify error when no quants exist
- **Preconditions:**
  - Product without any quants
- **Steps:**
  1. Scan product
  2. Confirm adjustment
- **Expected Result:** Line marked as erroneous

### Test Case 3.5: Insufficient Stock for Deduction
**Objective:** Verify error on excessive deduction
- **Preconditions:**
  - Total available: 20 units
- **Steps:**
  1. Scan to deduct 30 units
  2. Confirm adjustment
- **Expected Result:** Line marked as erroneous

## 4. Refresh Stock Tests

### Test Case 4.1: Current Stock Refresh
**Objective:** Verify current stock refresh
- **Steps:**
  1. Create adjustment
  2. Add stock moves outside adjustment
  3. Click Refresh Stock with "Current"
- **Expected Result:** On-hand quantities updated to current

### Test Case 4.2: Backdated Stock Refresh
**Objective:** Verify backdated stock calculation
- **Steps:**
  1. Select backdated option
  2. Choose date 7 days ago
  3. Apply refresh
- **Expected Result:** Quantities calculated as of selected date

### Test Case 4.3: Refresh Permission Check
**Objective:** Verify only authorized users can refresh
- **Steps:**
  1. Login as non-authorized user
  2. Try to refresh stock
- **Expected Result:** Access denied

### Test Case 4.4: Refresh State Restrictions
**Objective:** Verify refresh blocked in done/draft states
- **Steps:**
  1. Set adjustment to done
  2. Try to refresh
- **Expected Result:** Option not available

### Test Case 4.5: Inventory Date Update
**Objective:** Verify inventory date updates correctly
- **Steps:**
  1. Refresh with current option
  2. Check inventory_date field
- **Expected Result:** Current datetime set

## 5. Zero Stock for Non-Scanned Products

### Test Case 5.1: Auto Zero Lines Creation
**Objective:** Verify zero lines for unscanned products
- **Preconditions:**
  - Location has Products A, B, C
  - Only Product A scanned
- **Steps:**
  1. Confirm adjustment
- **Expected Result:** Zero lines created for B and C

### Test Case 5.2: Complete Location Reset
**Objective:** Verify all unscanned become zero on validation
- **Steps:**
  1. Validate adjustment
- **Expected Result:** Products B, C have 0 quantity

## 6. Location Restrictions

### Test Case 6.1: Single Location per Adjustment
**Objective:** Verify one location restriction
- **Steps:**
  1. Create adjustment for Location A
  2. Try to add Location B
- **Expected Result:** Not allowed

### Test Case 6.2: Parent-Child Locations
**Objective:** Verify separate adjustments needed
- **Steps:**
  1. Create adjustment for parent location
  2. Create adjustment for child location
- **Expected Result:** Two separate adjustments allowed

### Test Case 6.3: Active Adjustment Check
**Objective:** Verify only one active adjustment per location
- **Steps:**
  1. Create adjustment for Location A in draft
  2. Try to create another for Location A
- **Expected Result:** Validation error

## 7. Workflow State Tests

### Test Case 7.1: Draft to To Approve
**Objective:** Verify confirmation process
- **Steps:**
  1. Create adjustment with scanned lines
  2. Click Confirm
- **Expected Result:**
  - State changes to "To Approve"
  - Zero lines created
  - Lot lines computed

### Test Case 7.2: Approval Process
**Objective:** Verify approval by authorized user
- **Steps:**
  1. Login as approver
  2. Approve adjustment
- **Expected Result:**
  - State changes to "Approved"
  - Approved_by field set

### Test Case 7.3: Posting with Errors
**Objective:** Verify posting blocked with errors
- **Steps:**
  1. Create adjustment with error lines
  2. Try to post
- **Expected Result:**
  - Posting blocked
  - Error message in chatter

### Test Case 7.4: Successful Posting
**Objective:** Verify successful posting
- **Steps:**
  1. Post valid adjustment
- **Expected Result:**
  - Stock moves created
  - State changes to "Done"
  - Unit prices stored

### Test Case 7.5: Back to Draft
**Objective:** Verify reset to draft capability
- **Steps:**
  1. Cancel approved adjustment
  2. Reset to draft
- **Expected Result:** State changes back to draft

### Test Case 7.6: Difference Mismatch Check
**Objective:** Verify difference validation
- **Steps:**
  1. Create mismatch between line and lot differences
  2. Try to post
- **Expected Result:** Validation error

## 8. Stock Move and Valuation Tests

### Test Case 8.1: Stock Move Creation
**Objective:** Verify correct stock moves created
- **Steps:**
  1. Post adjustment with differences
- **Expected Result:**
  - Positive differences: inventory → location
  - Negative differences: location → inventory

### Test Case 8.2: Unit Price Storage
**Objective:** Verify unit prices stored in lines
- **Steps:**
  1. Post adjustment
  2. Check line unit_price field
- **Expected Result:** Current valuation price stored

### Test Case 8.3: Cost Analysis Report
**Objective:** Verify cost fetched from lines
- **Steps:**
  1. Generate cost analysis report
- **Expected Result:** Uses stored unit price, not current

### Test Case 8.4: Accounting Entry Creation
**Objective:** Verify accounting entries created
- **Steps:**
  1. Post adjustment
  2. Check account moves
- **Expected Result:** Proper accounting entries created

## 9. Security and Access Tests

### Test Case 9.1: Group Permissions
**Objective:** Verify group-based access
- **Steps:**
  1. Test with different user groups
- **Expected Result:** Actions restricted by group

### Test Case 9.2: Company Isolation
**Objective:** Verify multi-company isolation
- **Steps:**
  1. Create adjustments in different companies
- **Expected Result:** Adjustments isolated by company

## 10. Edge Cases and Error Handling

### Test Case 10.1: Concurrent Adjustments
**Objective:** Verify handling of concurrent scans
- **Steps:**
  1. Two users scan simultaneously
- **Expected Result:** Both scans recorded correctly

### Test Case 10.2: Large Volume Scanning
**Objective:** Verify performance with many items
- **Steps:**
  1. Scan 1000+ items
- **Expected Result:** System handles without timeout

### Test Case 10.3: Network Interruption
**Objective:** Verify data integrity on interruption
- **Steps:**
  1. Scan items
  2. Simulate network loss
- **Expected Result:** Partial data saved correctly

## Test Execution Matrix

| Test Category | Critical | High | Medium | Low |
|--------------|----------|------|--------|-----|
| Barcode Scanning | 1.1, 1.2 | 1.3, 1.4 | 1.5 | 1.6 |
| Negative Stock | 2.1 | 2.2 | - | - |
| Lot Selection | 3.1, 3.2 | 3.3, 3.4, 3.5 | - | - |
| Refresh Stock | 4.1, 4.2 | 4.3 | 4.4, 4.5 | - |
| Zero Stock | 5.1, 5.2 | - | - | - |
| Location | 6.1 | 6.2, 6.3 | - | - |
| Workflow | 7.1, 7.3, 7.4 | 7.2, 7.5, 7.6 | - | - |
| Stock Move | 8.1, 8.2 | 8.3, 8.4 | - | - |
| Security | 9.1 | 9.2 | - | - |
| Edge Cases | - | 10.1 | 10.2, 10.3 | - |

## Test Data Requirements

### Products
- Product A: With barcode, trackable by lot
- Product B: With barcode, no tracking
- Product C: No barcode
- Product D: Serial tracked

### Lots
- LOT001, LOT002, LOT003 for Product A
- Different in_dates for FIFO testing

### Locations
- WH/Stock (parent)
- WH/Stock/Shelf1 (child)
- WH/Stock/Shelf2 (child)

### Users
- admin: Full access
- user_scanner: Scanning access only
- user_approver: Approval rights
- user_viewer: Read-only access

### Initial Stock Levels
- Positive stock scenarios
- Negative stock scenarios
- Zero stock scenarios
- Mixed stock scenarios

## Automation Strategy
- Use Odoo test framework
- Mock barcode scanning events
- Automated workflow progression
- Assertion-based validation
- Transaction rollback for isolation