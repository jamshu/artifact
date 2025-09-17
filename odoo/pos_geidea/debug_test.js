// Copy and paste this in the browser console to test the restrictions

// 1. Check if the module is loaded
console.log('=== Geidea Module Debug ===');
console.log('Current POS:', window.pos || 'No POS found');

// 2. Check current order and payment lines
if (window.pos) {
    const order = window.pos.get_order();
    console.log('Current order:', order);
    
    if (order) {
        console.log('Payment lines:', order.paymentlines);
        
        // Check each payment line
        order.paymentlines.forEach((line, index) => {
            console.log(`Payment line ${index}:`, {
                payment_method: line.payment_method.name,
                use_payment_terminal: line.payment_method.use_payment_terminal,
                status: line.get_payment_status(),
                terminal_status: line.payment_method.payment_terminal ? line.payment_method.payment_terminal.status : 'no terminal'
            });
        });
    }
}

// 3. Test the helper functions if available
if (typeof window.hasWaitingGeideaPaymentsInCurrentOrder !== 'undefined') {
    console.log('Helper functions available, testing...');
    if (window.pos) {
        console.log('Has waiting Geidea payments (current):', window.hasWaitingGeideaPaymentsInCurrentOrder(window.pos));
        console.log('Has waiting Geidea payments (all):', window.hasWaitingGeideaPayments(window.pos));
    }
} else {
    console.log('Helper functions not available - module may not be loaded');
    console.log('Check for "Geidea payment restrictions module loaded successfully" message above');
}

// 4. Check if restrictions are working
console.log('To test restrictions:');
console.log('1. Add a Geidea payment line');
console.log('2. Click "Send to Terminal"');
console.log('3. Try clicking Back button or Orders button');
console.log('4. Check console logs for "Geidea:" messages');

// 5. Quick test function
window.testGeideaRestrictions = function() {
    if (window.pos) {
        const order = window.pos.get_order();
        if (order && order.paymentlines.length > 0) {
            // Simulate setting a Geidea payment to waiting
            const geideaLine = order.paymentlines.find(line => 
                line.payment_method.use_payment_terminal === 'geidea'
            );
            
            if (geideaLine) {
                console.log('Setting Geidea line to waiting status...');
                geideaLine.set_payment_status('waiting');
                console.log('Status set to:', geideaLine.get_payment_status());
                
                // Test the helper function
                if (window.hasWaitingGeideaPaymentsInCurrentOrder) {
                    console.log('Helper function result:', window.hasWaitingGeideaPaymentsInCurrentOrder(window.pos));
                }
                
                console.log('Now try clicking Back button or Orders button to test restrictions.');
            } else {
                console.log('No Geidea payment line found. Add one first.');
            }
        } else {
            console.log('No payment lines found. Add a Geidea payment first.');
        }
    }
};

console.log('=== Debug functions ready ===');
console.log('Run: window.testGeideaRestrictions() to test');
