odoo.define('pos_geidea.models', function(require) {
    'use strict';

    var models = require('point_of_sale.models');
    const { register_payment_method } = require('point_of_sale.models');
    const GeideaPaymentInterface = require('pos_geidea.payment');

   
    models.load_fields('pos.payment.method', [
        'use_payment_terminal',
        'geidea_port',
        'geidea_connection_mode',
        'geidea_com_name',
        'geidea_baud_rate',
        'geidea_data_bits',
        'geidea_parity',
        'geidea_ip_address',
        'geidea_print_settings',
        'geidea_app_id'
    ]);

    // Extend payment line model
    var _super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function(attributes, options) {
            _super_paymentline.initialize.apply(this, arguments);
            
            // Initialize Geidea-specific fields with default values
            this.card_number = '';
            this.rrn = '';
            this.transaction_id = '';
            this.terminal_id = '';
            this.card_type = '';
            this.payment_status = 'pending'; // Always start with pending status
            this.transaction_type = '';
            this.transaction_response = '';
            this.transaction_date = '';
            this.pos_entry_mode = '';
            
            console.log('Geidea Payment line initialized with status:', this.payment_status);
        },
        
        init_from_JSON: function(json) {
            _super_paymentline.init_from_JSON.apply(this, arguments);
            
            // Load Geidea-specific fields from JSON with defaults
            this.card_number = json.card_number || '';
            this.rrn = json.rrn || '';
            this.transaction_id = json.transaction_id || '';
            this.terminal_id = json.terminal_id || '';
            this.card_type = json.card_type || '';
            this.payment_status = json.payment_status || 'pending'; // Default to pending if not set
            this.transaction_type = json.transaction_type || '';
            this.transaction_response = json.transaction_response || '';
            this.transaction_date = json.transaction_date || '';
            this.pos_entry_mode = json.pos_entry_mode || '';
            
            console.log('GeideaPayment line loaded from JSON with status:', this.payment_status);
        },
        
        export_as_JSON: function() {
            var json = _super_paymentline.export_as_JSON.apply(this, arguments);
            json.card_number = this.card_number;
            json.rrn = this.rrn;
            json.transaction_id = this.transaction_id;
            json.terminal_id = this.terminal_id;
            json.card_type = this.card_type;
            json.payment_status = this.payment_status;
            json.transaction_type = this.transaction_type;
            json.transaction_response = this.transaction_response;
            json.transaction_date = this.transaction_date;
            json.pos_entry_mode = this.pos_entry_mode;
            return json;
        }
    });

    

    register_payment_method('geidea', GeideaPaymentInterface);

    return models;
});
