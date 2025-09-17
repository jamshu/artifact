// Debug script for payment status persistence bug
// Paste this in browser console to test the fix

console.log('=== Payment Status Bug Debug ===');

// Function to check payment interface status
window.checkPaymentInterfaceStatus = function() {
    const pos = window.pos;
    if (!pos) {
        console.log('No POS found');
        return;
    }
    
    const geideaMethod = pos.payment_methods.find(method => 
        method.use_payment_terminal === 'geidea'
    );
    
    if (geideaMethod && geideaMethod.payment_terminal) {
        console.log('Geidea Payment Interface Status:', geideaMethod.payment_terminal.status);
        console.log('Geidea Payment Interface Object:', geideaMethod.payment_terminal);
    } else {
        console.log('No Geidea payment method or interface found');
    }
    
    // Check current order payment lines
    const order = pos.get_order();
    if (order) {
        console.log('Current order payment lines:');
        order.paymentlines.forEach((line, index) => {
            console.log(`Line ${index}:`, {
                method: line.payment_method.name,
                status: line.get_payment_status(),
                amount: line.amount,
                is_geidea: line.payment_method.use_payment_terminal === 'geidea'
            });
        });
    }
};

// Function to simulate the bug scenario
window.testPaymentStatusBug = function() {
    const pos = window.pos;
    if (!pos) {
        console.log('No POS found');
        return;
    }
    
    console.log('=== Testing Payment Status Bug ===');
    
    // Step 1: Check current state
    console.log('Step 1: Current state');
    window.checkPaymentInterfaceStatus();
    
    // Step 2: Create new order
    console.log('Step 2: Creating new order');
    pos.add_new_order();
    
    // Step 3: Check state after new order
    console.log('Step 3: State after new order');
    window.checkPaymentInterfaceStatus();
    
    // Step 4: Add Geidea payment line
    const geideaMethod = pos.payment_methods.find(method => 
        method.use_payment_terminal === 'geidea'
    );
    
    if (geideaMethod) {
        console.log('Step 4: Adding Geidea payment line');
        const order = pos.get_order();
        const line = order.add_paymentline(geideaMethod);
        
        console.log('Step 5: Payment line added, status:', line ? line.get_payment_status() : 'no line');
        
        // Check if line has incorrect status
        if (line && line.get_payment_status() === 'done') {
            console.error('🚨 BUG DETECTED: New payment line has "done" status without processing!');
        } else {
            console.log('✅ Payment line has correct initial status');
        }
    } else {
        console.log('No Geidea payment method found');
    }
};

// Function to reset payment interface status (for testing)
window.resetGeideaInterface = function() {
    const pos = window.pos;
    if (!pos) {
        console.log('No POS found');
        return;
    }
    
    const geideaMethod = pos.payment_methods.find(method => 
        method.use_payment_terminal === 'geidea'
    );
    
    if (geideaMethod && geideaMethod.payment_terminal) {
        console.log('Resetting Geidea interface status from:', geideaMethod.payment_terminal.status);
        geideaMethod.payment_terminal.status = 'pending';
        console.log('Reset to:', geideaMethod.payment_terminal.status);
    }
};

// Function to monitor payment line creation
const originalAddPaymentline = window.pos && window.pos.get_order().add_paymentline;
if (originalAddPaymentline && window.pos) {
    window.pos.get_order().add_paymentline = function(method) {
        console.log('Adding payment line for method:', method.name);
        console.log('Method use_payment_terminal:', method.use_payment_terminal);
        
        if (method.use_payment_terminal === 'geidea') {
            console.log('Geidea interface status before adding line:', 
                method.payment_terminal ? method.payment_terminal.status : 'no interface');
        }
        
        const result = originalAddPaymentline.call(this, method);
        
        if (result && method.use_payment_terminal === 'geidea') {
            console.log('New Geidea payment line status:', result.get_payment_status());
            if (result.get_payment_status() === 'done') {
                console.error('🚨 BUG: New payment line created with "done" status!');
            }
        }
        
        return result;
    };
}

console.log('Payment status debug functions ready:');
console.log('- window.checkPaymentInterfaceStatus()');
console.log('- window.testPaymentStatusBug()');
console.log('- window.resetGeideaInterface()');

// Auto-run initial check
window.checkPaymentInterfaceStatus();