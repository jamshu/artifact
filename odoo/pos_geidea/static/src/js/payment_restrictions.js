odoo.define('pos_geidea.payment_restrictions', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const TicketButton = require('point_of_sale.TicketButton');
    const TicketScreen = require('point_of_sale.TicketScreen');
    const models = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const { Gui } = require('point_of_sale.Gui');
    const { _t } = require('web.core');
    const loggingClient = require('pos_geidea.logging_client');





    function hasDoneGeideaPaymentsInCurrentOrder(pos) {
        const order = pos.get_order();
        if (!order) {
            console.log('Geidea: No current order');
            return false;
        }

        const hasDone = order.paymentlines.some(line => {
            const paymentMethod = line.payment_method;
            const isGeidea = paymentMethod.use_payment_terminal === 'geidea';
            const status = line.get_payment_status();




            return (
                isGeidea && status === 'done'
            );
        });

        return hasDone;
    }


    /**
     * Helper function to check current order only for waiting Geidea payments
     */
    function hasWaitingGeideaPaymentsInCurrentOrder(pos) {
        const order = pos.get_order();
        if (!order) {
            console.log('Geidea: No current order');
            return false;
        }

        const hasWaiting = order.paymentlines.some(line => {
            const paymentMethod = line.payment_method;
            const isGeidea = paymentMethod.use_payment_terminal === 'geidea';
            const status = line.get_payment_status();
            const terminalStatus = paymentMethod.payment_terminal && paymentMethod.payment_terminal.status;
            
            if (isGeidea) {
                console.log('Geidea: Found Geidea payment line - status:', status, 'terminal status:', terminalStatus);
                console.log('Geidea: Payment method object:', paymentMethod);
                console.log('Geidea: Payment line object:', line);
            }
            
            return (
                isGeidea &&
                (status === 'waiting' || terminalStatus === 'waiting')
            );
        });
        
        console.log('Geidea: hasWaitingGeideaPaymentsInCurrentOrder =', hasWaiting);
        return hasWaiting;
    }

    /**
     * Helper function to check all orders for waiting Geidea payments
     */
    function hasWaitingGeideaPayments(pos) {
        const orders = pos.get_order_list();
        return orders.some(order => {
            return order.paymentlines.some(line => {
                const paymentMethod = line.payment_method;
                return (
                    paymentMethod.use_payment_terminal === 'geidea' &&
                    (line.get_payment_status() === 'waiting' || 
                     (paymentMethod.payment_terminal && paymentMethod.payment_terminal.status === 'waiting'))
                );
            });
        });
    }

    // We'll handle navigation restrictions in the specific components instead of PosComponent

    // Override TicketButton to prevent Orders access during payment processing
    const GeideaTicketButton = (TicketButton) =>
        class extends TicketButton {
            onClick() {
                // Check if we're in PaymentScreen and have waiting payments
                if (hasWaitingGeideaPaymentsInCurrentOrder(this.env.pos)) {
                    Gui.showPopup('ErrorPopup', {
                        title: _t('Payment Processing'),
                        body: _t('Cannot access orders while payment is being processed on terminal. Please wait for the transaction to complete or cancel it on the terminal.')
                    });
                    return;
                }
                super.onClick();
            }
        };

    // Override TicketScreen to prevent new order creation when payments are processing
    const GeideaTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            _onCreateNewOrder() {
                if (hasWaitingGeideaPayments(this.env.pos)) {
                    Gui.showPopup('ErrorPopup', {
                        title: _t('Payment Processing'),
                        body: _t('Cannot create new order while there are pending terminal payments. Please complete or cancel all terminal transactions first.')
                    });
                    return;
                }
                super._onCreateNewOrder();
            }
        };

    // Extend PaymentScreen for additional restrictions
    const GeideaPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }

            /**
             * Override showScreen to handle back navigation and other screen changes
             */
            showScreen(name, props) {
                console.log('Geidea PaymentScreen: showScreen called with name:', name);
                 if (hasDoneGeideaPaymentsInCurrentOrder(this.env.pos)) {
                    if (name === 'ProductScreen') {
                        console.log('Geidea: Blocking navigation to ProductScreen - payment Done');
                        Gui.showPopup('ErrorPopup', {
                            title: _t('Payment Completed'),
                            body: _t('Cannot go back while payment Completed on terminal. Please Create a new order if you need buy more products.')
                        });
                        return;
                    }


                }


                // Prevent navigation from PaymentScreen when payments are processing
                if (hasWaitingGeideaPaymentsInCurrentOrder(this.env.pos)) {
                    if (name === 'ProductScreen') {
                        console.log('Geidea: Blocking navigation to ProductScreen - payment in progress');
                        window.geideaLogger && window.geideaLogger.logRestriction(
                            'back_navigation', true, 'Payment in progress', 
                            { target_screen: name, current_screen: 'PaymentScreen' }
                        );
                        Gui.showPopup('ErrorPopup', {
                            title: _t('Payment Processing'),
                            body: _t('Cannot go back while payment is being processed on terminal. Please wait for the transaction to complete or cancel it on the terminal.')
                        });
                        return;
                    }
                    
                    if (name === 'TicketScreen') {
                        console.log('Geidea: Blocking navigation to TicketScreen - payment in progress');
                        window.geideaLogger && window.geideaLogger.logRestriction(
                            'orders_navigation', true, 'Payment in progress',
                            { target_screen: name, current_screen: 'PaymentScreen' }
                        );
                        Gui.showPopup('ErrorPopup', {
                            title: _t('Payment Processing'),
                            body: _t('Cannot access orders while payment is being processed on terminal. Please wait for the transaction to complete or cancel it on the terminal.')
                        });
                        return;
                    }
                }
                
                console.log('Geidea PaymentScreen: Allowing navigation to', name);
                super.showScreen(name, props);
            }

            /**
             * Override _isOrderValid to prevent the electronic_payment_in_progress check
             * from triggering cancellation for Geidea payments
             */
            async _isOrderValid(isForceValidate) {
                // Check for waiting Geidea payments and show our custom message instead
                if (hasWaitingGeideaPaymentsInCurrentOrder(this.env.pos)) {
                    console.log('Geidea: Blocking order validation - payment in progress');
                    Gui.showPopup('ErrorPopup', {
                        title: _t('Payment Processing'),
                        body: _t('Cannot complete order while payment is being processed on terminal. Please wait for the transaction to complete or cancel it on the terminal.')
                    });
                    return false;
                }
                
                // Call the original method
                return super._isOrderValid(isForceValidate);
            }

            /**
             * Override toggleIsToInvoice to prevent changes during payment processing
             */
            toggleIsToInvoice() {
                if (hasWaitingGeideaPaymentsInCurrentOrder(this.env.pos)) {
                    Gui.showPopup('ErrorPopup', {
                        title: _t('Payment Processing'),
                        body: _t('Cannot modify order settings while payment is being processed on terminal.')
                    });
                    return;
                }
                super.toggleIsToInvoice();
            }

            /**
             * Override deletePaymentLine to prevent deletion during processing
             */
            deletePaymentLine(event) {
                const { cid } = event.detail;
                const order = this.env.pos.get_order();
                const line = order.paymentlines.find(line => line.cid === cid);
                
                if (line && 
                    line.payment_method.use_payment_terminal === 'geidea' && 
                    (line.get_payment_status() === 'waiting' || 
                     (line.payment_method.payment_terminal && line.payment_method.payment_terminal.status === 'waiting'))) {
                    Gui.showPopup('ErrorPopup', {
                        title: _t('Payment Processing'),
                        body: _t('Cannot delete payment line while it is being processed on terminal. Please wait for completion or cancel on the terminal.')
                    });
                    return;
                }
                super.deletePaymentLine(event);
            }
        };

    // Extend Order model to handle electronic payment checks for Geidea specially
    const _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        electronic_payment_in_progress: function() {
            const hasWaitingGeidea = this.get_paymentlines().some(function(pl) {
                return pl.payment_method.use_payment_terminal === 'geidea' &&
                       pl.payment_status === 'waiting';
            });
            
            // If we have waiting Geidea payments, don't treat them as blocking electronic payments
            // This prevents the automatic cancellation popup
            if (hasWaitingGeidea) {
                // Check for non-Geidea electronic payments in progress
                return this.get_paymentlines().some(function(pl) {
                    if (pl.payment_status) {
                        // Exclude Geidea payments from this check
                        if (pl.payment_method.use_payment_terminal === 'geidea') {
                            return false;
                        }
                        return !['done', 'reversed'].includes(pl.payment_status);
                    } else {
                        return false;
                    }
                });
            }
            
            // Call original method for non-Geidea scenarios
            return _super_order.electronic_payment_in_progress.call(this);
        }
    });

    // Register the extended components
    Registries.Component.extend(TicketButton, GeideaTicketButton);
    Registries.Component.extend(TicketScreen, GeideaTicketScreen);
    Registries.Component.extend(PaymentScreen, GeideaPaymentScreen);

    // Expose helper functions globally for debugging
    window.hasWaitingGeideaPaymentsInCurrentOrder = hasWaitingGeideaPaymentsInCurrentOrder;
    window.hasWaitingGeideaPayments = hasWaitingGeideaPayments;
    
    console.log('Geidea payment restrictions module loaded successfully');

    return {
        GeideaTicketButton,
        GeideaTicketScreen,
        GeideaPaymentScreen,
        hasWaitingGeideaPaymentsInCurrentOrder,
        hasWaitingGeideaPayments
    };
});
