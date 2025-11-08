# Geidea Payment Terminal Restrictions

This module now includes restrictions to prevent user actions when payments are being processed on the Geidea terminal.

## Features Implemented

### Payment Screen Restrictions
When a payment line has been sent to the terminal (status = 'waiting'):

1. **Back Navigation Blocked**: Users cannot navigate back to the product screen
2. **Payment Line Deletion Blocked**: Cannot delete payment lines being processed
3. **Order Settings Locked**: Cannot toggle invoice settings or modify order details
4. **Visual Feedback**: Warning message appears indicating payment is processing

### Product Screen Restrictions
When there are pending terminal payments in any order:

1. **New Order Creation Blocked**: Cannot create new orders
2. **Order Switching Blocked**: Cannot switch between orders
3. **Clear Error Messages**: Informative popups explain why actions are restricted

### Payment Status Bug Fix
🚨 **Critical Bug Fixed**: Payment lines showing as 'done' without processing

**Problem**: Sometimes new payment lines would automatically show as successful even before card swiping
**Root Cause**: Payment interface status was persisting across different orders
**Solution**: 
- Reset payment interface status for each new payment
- Ensure payment lines initialize with 'pending' status
- Clean up interface state after payment completion

## Technical Implementation

### Files Modified/Created:
- `static/src/js/payment_restrictions.js` - Main restriction logic
- `static/src/js/payment_status_fix.js` - Fix for payment status persistence bug
- `static/src/xml/pos_geidea.xml` - Visual feedback templates
- `static/src/css/pos_geidea.scss` - Styling for warnings and disabled states
- `__manifest__.py` - Added new JS files to assets
- `debug_payment_status.js` - Debug script for testing payment status bug

### Payment Status Detection:
The system checks for:
- `line.get_payment_status() === 'waiting'`
- `paymentMethod.payment_terminal.status === 'waiting'`

### Key Functions:
- `hasWaitingGeideaPaymentsInCurrentOrder()` - Checks current order for waiting payments
- `hasWaitingGeideaPayments()` - Checks all orders for waiting payments

### Extended Components:
- `PosComponent` - Intercepts `showScreen` calls to prevent navigation
- `TicketButton` - Prevents Orders button clicks during processing
- `TicketScreen` - Prevents new order creation from Orders screen
- `PaymentScreen` - Additional restrictions for payment operations

## Testing Checklist

### Basic Functionality:
- [ ] Payment can be sent to terminal normally
- [ ] Terminal payment processing works as before
- [ ] Payment completion updates status correctly

### Restriction Testing:
- [ ] Back button is disabled/blocked during payment processing
- [ ] Warning message appears when payment is processing  
- [ ] Cannot delete payment line during processing
- [ ] Cannot create new order when payments are pending
- [ ] Cannot switch orders when payments are pending
- [ ] Error popups show appropriate messages

### Edge Cases:
- [ ] Multiple payment lines with different statuses
- [ ] Payment cancellation/timeout restores normal operation
- [ ] Payment completion restores normal operation
- [ ] Mixed payment methods (Geidea + Cash) work correctly

### Visual Feedback:
- [ ] Warning banner appears during processing
- [ ] Back button visually appears disabled
- [ ] Processing spinner shows on payment button
- [ ] CSS styling applied correctly

## User Experience

### Normal Flow:
1. Add products to cart
2. Go to payment screen
3. Add Geidea payment method
4. Click "Send to Terminal" - button shows "Processing..." with spinner
5. Warning banner appears: "Payment Processing: Terminal payment in progress..."
6. Back button becomes disabled/grayed out
7. Terminal processes payment
8. On completion, restrictions are lifted and normal operation resumes

### Restricted Actions:
When payment is processing, users see error messages for:
- "Cannot go back while payment is being processed on terminal..."
- "Cannot create new order while there are pending terminal payments..."
- "Cannot delete payment line while it is being processed on terminal..."
- "Cannot switch orders while there are pending terminal payments..."

## Configuration

No additional configuration is required. The restrictions are automatically active when:
1. The pos_geidea module is installed
2. Payment methods are configured with `use_payment_terminal = 'geidea'`
3. Payment status reaches 'waiting' state

## Troubleshooting

### Step 1: Check if module is loaded
1. Open browser console (F12)
2. Paste the content from `debug_test.js` file and run it
3. Look for "Geidea Module Debug" messages
4. Verify payment lines and their statuses are shown

### Step 2: Test restrictions manually
1. Run `window.testGeideaRestrictions()` in console
2. This will set a Geidea payment to 'waiting' status
3. Try clicking Back/Orders buttons
4. Check for "Geidea:" console messages

### Step 3: If restrictions don't work:
1. **Check browser console** for JS errors
2. **Verify payment_restrictions.js is loaded** in Network tab
3. **Confirm payment status** is being set to 'waiting' correctly
4. **Check payment method configuration**: `use_payment_terminal === 'geidea'`
5. **Look for console logs** starting with "Geidea:"

### Step 4: Common Issues
1. **Module not loaded**: Check `__manifest__.py` includes the JS file
2. **Status not updating**: Verify payment interface sets status to 'waiting'
3. **Wrong payment method**: Ensure `use_payment_terminal === 'geidea'`
4. **Order model override**: Check if Order.electronic_payment_in_progress is working
5. **Component extensions**: Verify Registries.Component.extend calls are working

### Step 5: Test Payment Status Bug Fix:
1. **Paste debug_payment_status.js content** in browser console
2. **Run**: `window.testPaymentStatusBug()`
3. **Check**: New payment lines should have 'pending' status, NOT 'done'
4. **Look for**: "🚨 BUG DETECTED" messages (should not appear)
5. **Verify**: Console shows "Geidea payment status fix module loaded"

### Step 6: If restrictions are too strict:
- The restrictions automatically lift when payment status changes from 'waiting' to 'done' or 'retry'
- Manual terminal cancellation should update the status accordingly
- Check the Order model extension is properly filtering Geidea payments
