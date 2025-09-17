odoo.define('pos_geidea.payment_status_fix', function(require) {
    'use strict';

    var models = require('point_of_sale.models');
    const { register_payment_method } = require('point_of_sale.models');

    // Override the original payment interface to fix status persistence
    const GeideaPaymentInterface = require('pos_geidea.payment');
    
    const FixedGeideaPaymentInterface = GeideaPaymentInterface.extend({
        init: function(pos, payment_method) {
            this._super.apply(this, arguments);
            // Reset status for each new interface instance
            this.status = 'pending';
            this.terminal = null;
            
            console.log('Geidea Payment Interface initialized with fresh status: pending');
        },

        send_payment_request: async function(cid) {
            // Ensure we start with a clean state for each payment
            this.status = 'pending';
            const line = this.pos.get_order().get_paymentline(cid);
            
            console.log('Geidea: send_payment_request called for line:', cid);
            console.log('Geidea: Line current status:', line ? line.get_payment_status() : 'no line');
            console.log('Geidea: Interface status reset to:', this.status);
            
            // Ensure the payment line starts with correct status
            if (line) {
                line.set_payment_status('pending');
                console.log('Geidea: Line status reset to pending');
            }
            
            return this._super.apply(this, arguments);
        },

        _setStatus(status, line) {
            console.log('Geidea: _setStatus called with:', status, 'for line:', line ? line.cid : 'no line');
            this.status = status;
            if (line) {
                line.set_payment_status(status);
                console.log('Geidea: Line status updated to:', line.get_payment_status());
            }
        },

        _cleanup() {
            console.log('Geidea: Cleaning up payment interface');
            // Reset status after cleanup
            const result = this._super.apply(this, arguments);
            
            // Reset the interface status after cleanup to prevent persistence
            setTimeout(() => {
                if (this.status === 'done') {
                    console.log('Geidea: Resetting interface status from done to pending after cleanup');
                        this.status = 'pending';
                }
            }, 100);
            
            return result;
        }
    });

    // Also fix the payment line model to ensure proper initialization
    var _super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function(attributes, options) {
            _super_paymentline.initialize.apply(this, arguments);
            
            // Ensure Geidea payment lines start with proper clean state
            if (this.payment_method && this.payment_method.use_payment_terminal === 'geidea') {
                console.log('Geidea: Initializing new Geidea payment line with clean state');
                this.card_number = '';
                this.rrn = '';
                this.transaction_id = '';
                this.terminal_id = '';
                this.card_type = '';
                this.payment_status = 'pending'; // Explicitly set to pending for Geidea
                this.transaction_type = '';
                this.transaction_response = '';
                this.transaction_date = '';
                this.pos_entry_mode = '';
                
                // Make sure the payment status is set correctly
                this.set_payment_status('pending');
                console.log('Geidea: Payment line initialized with status:', this.get_payment_status());
            } else {
                // For non-Geidea payments, use the original initialization
                this.card_number = '';
                this.rrn = '';
                this.transaction_id = '';
                this.terminal_id = '';
                this.card_type = '';
                this.payment_status = '';
                this.transaction_type = '';
                this.transaction_response = '';
                this.transaction_date = '';
                this.pos_entry_mode = '';
            }
        },

        // Override set_payment_status to add logging for Geidea payments
        set_payment_status: function(status) {
            if (this.payment_method && this.payment_method.use_payment_terminal === 'geidea') {
                console.log('Geidea: Payment line status changing from', this.payment_status, 'to', status);
            }
            return _super_paymentline.set_payment_status.call(this, status);
        }
    });

    // Re-register the payment method with the fixed interface
    register_payment_method('geidea', FixedGeideaPaymentInterface);

    console.log('Geidea payment status fix module loaded');

    return FixedGeideaPaymentInterface;
});