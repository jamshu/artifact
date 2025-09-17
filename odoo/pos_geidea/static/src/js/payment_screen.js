odoo.define('pos_geidea.payment_screen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const GeideaPaymentScreen = PaymentScreen => class extends PaymentScreen {
        constructor() {
            super(...arguments);
            
            // Track current order to detect changes
            this._currentOrderId = null;
            
            console.log('Geidea PaymentScreen extension loaded');
        }

        // Minimal reset function that doesn't depend on complex lookups
        _tryResetGeideaInterface() {
            try {
                // Try to find and reset Geidea payment interface
                if (window.geideaPaymentInterface && 
                    typeof window.geideaPaymentInterface.resetInterface === 'function') {
                    console.log('Resetting global Geidea payment interface');
                    window.geideaPaymentInterface.resetInterface();
                    return;
                }
                
                // Alternative: Look for any interface in the POS that might be Geidea
                const pos = this.env.pos;
                if (pos && pos.payment_interfaces_by_name) {
                    const geideaInterface = pos.payment_interfaces_by_name['geidea'];
                    if (geideaInterface && typeof geideaInterface.resetInterface === 'function') {
                        console.log('Resetting Geidea interface from POS registry');
                        geideaInterface.resetInterface();
                    }
                }
            } catch (error) {
                console.log('Could not reset Geidea interface (this is normal if not initialized yet):', error.message);
            }
        }

        // Override addNewPaymentLine with minimal intervention
        addNewPaymentLine({ detail: paymentMethod }) {
            try {
                // For Geidea payment methods, try a gentle reset
                if (paymentMethod && paymentMethod.use_payment_terminal === 'geidea') {
                    console.log('Processing Geidea payment method:', paymentMethod.name);
                    this._tryResetGeideaInterface();
                }
            } catch (error) {
                console.warn('Non-critical error in Geidea payment processing:', error);
            }
            
            // Always call the parent method
            return super.addNewPaymentLine({ detail: paymentMethod });
        }

        // Override willStart to initialize
        willStart() {
            const result = super.willStart();
            
            try {
                if (this.currentOrder) {
                    this._currentOrderId = this.currentOrder.uid;
                }
            } catch (error) {
                console.warn('Error initializing Geidea payment screen:', error);
            }
            
            return result;
        }
    };

    // Only extend if PaymentScreen is available
    if (PaymentScreen) {
        Registries.Component.extend(PaymentScreen, GeideaPaymentScreen);
        console.log('Geidea PaymentScreen extension registered successfully');
    } else {
        console.warn('PaymentScreen not available, skipping Geidea extension');
    }

    return GeideaPaymentScreen;
});
