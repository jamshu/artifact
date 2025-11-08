odoo.define('pos_geidea.payment', function(require) {
    'use strict';

    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const { Gui } = require('point_of_sale.Gui');
    const { _t } = require('web.core');

    const GeideaPaymentInterface = PaymentInterface.extend({
        init: function(pos, payment_method) {
            this._super.apply(this, arguments);
            this.terminal = null;
            this.payment_method = payment_method;
            this.pos = pos;
            this.status = 'pending';
            
            // Store global reference for other components to access
            window.geideaPaymentInterface = this;
        },

        _setStatus(status, line) {
            this.status = status;
            if (line) {
                line.set_payment_status(status);
            }
        },

        send_payment_request: async function(cid) {
            this._super.apply(this, arguments);
            const line = this.pos.get_order().get_paymentline(cid);
            
            // CRITICAL: Reset status for new payment request
            this.status = 'pending';
            
            console.log('Processing Geidea payment for line:', line, 'Current status:', this.status);
            
            if (!line || !this._validateConnection()) {
                this._setStatus('retry', line);
                return false;
            }

            // Ensure the payment line starts with pending status
            line.set_payment_status('pending');
            
            try {
                // Ensure complete cleanup before starting new payment
                await this._cleanup();
                
                // Small delay to ensure cleanup is complete
                await new Promise(resolve => setTimeout(resolve, 100));

                this._setStatus('waiting', line);

                await this._initializeConnection();
                await this._processPayment(line);
                
                return true; // Don't set done here, let _updatePaymentLine handle it
            } catch (error) {
                this._setStatus('retry', line);
                this._handleError(error);
                return false;
            }
        },

        send_payment_cancel: function(order, cid) {
            
            
            Gui.showPopup('ConfirmPopup', {
                title: _t('Cancel Payment'),
                body: _t('Please cancel the payment directly on the terminal.'),
                cancelText: _t('Close'),
                confirmText: _t('Ok')
            });

            return Promise.resolve(true);
        },

        _validateConnection() {
            // Check if payment method is configured for Geidea
            if (this.payment_method.use_payment_terminal !== 'geidea') {
                return false; // Silently ignore non-Geidea payment methods
            }

            // Only show errors for Geidea payment methods that are misconfigured
            
            if (!this.payment_method.geidea_port) {
                Gui.showPopup('ErrorPopup', {
                    title: _t('Configuration Error'),
                    body: _t('Terminal port not configured')
                });
                
                return false;
            }

            return true;
        },

        _initializeConnection() {
            return new Promise((resolve, reject) => {
                try {
                    // Ensure no existing connection
                    if (this.terminal) {
                        this._cleanup().then(() => {
                            this._createNewConnection(resolve, reject);
                        });
                    } else {
                        this._createNewConnection(resolve, reject);
                    }
                } catch (error) {
                    reject(error);
                }
            });
        },

        _createNewConnection(resolve, reject) {
            const wsUrl = `ws://localhost:${this.payment_method.geidea_port}/messages`;
            
            this.terminal = new WebSocket(wsUrl);
            
            this.terminal.onopen = () => {
                const data = this._getConnectionData();
                this.terminal.send(JSON.stringify(data));
                resolve();
            };
            
            this.terminal.onerror = (error) => {
                console.error('WebSocket connection error:', error);
                reject(error);
            };
        },

        _processPayment(line) {
            return new Promise((resolve, reject) => {
                console.log('Processing Geidea payment for line:', line);

                this.terminal.onmessage = (message) => {
                    try {
                        const data = JSON.parse(message.data);
                        console.log('Received from Geidea terminal:', data);
                        
                        if (data.Event === 'OnDataReceive') {
                            const result = JSON.parse(data.JsonResult);
                            if (result.TransactionResponseEnglish === 'APPROVED') {
                                console.log("Geidea payment approved:", result)
                                this._updatePaymentLine(line, result);
                                this._cleanup().then(() => {
                                    console.log("cleaning up and Payment line updated, resolving payment");
                                    resolve();
                                    });


                            }
                            else if (result.TransactionResponseEnglish && result.TransactionResponseEnglish !== 'APPROVED') {
                                 console.log("Geidea payment Declined:", result)
                                 this._setStatus('retry', line);
                                 reject(new Error('Payment Declined'));
                            }
                        } else if (data.Event === 'OnTerminalStatus') {
                            console.log("Geidea terminal status:", data);
                            if (data.TerminalStatus === 'BUSY'){
                                console.log("Geidea terminal busy, retrying payment");
                                this._setStatus('retry', line);
                                reject(new Error('Payment terminal busy'));
                                }
                            }

                        else if (data.Event === 'OnError') {
                            console.error("Geidea terminal error:", data);
                            if (terminal.status !== 'done') {
                             this._setStatus('retry', line);
                             reject(new Error('Payment terminal error'));
                            }



                        } else if (data.Event === 'OnTerminalAction') {
                            console.warn("Geidea terminal action:", data);
                            // Add handling for different terminal actions
                            if (data.TerminalAction === 'CARD_READ_ERROR' || data.TerminalAction === 'IDLE_SCREEN') {
                                this._setStatus('retry', line);
                                reject(new Error(data.OptionalMessage || `Terminal Error: ${data.TerminalAction}`));
                            } else if (data.TerminalAction === 'USER_CANCELLED_AND_TIMEOUT') {
                                this._setStatus('retry', line);
                                reject(new Error('Payment cancelled by user'));
                            }
                        }
                    } catch (error) {
                        console.error("Error processing Geidea message:", error);
                        this._setStatus('retry', line);
                        reject(error);
                    }
                };

                this.terminal.onerror = (error) => {
                    console.error("Geidea terminal connection error:", error);
                    this._setStatus('retry', line);
                    reject(error);
                };

                // Send payment request
                const paymentRequest = {
                    "Event": "TRANSACTION",
                    "Operation": "PURCHASE",
                    "Amount": line.amount.toFixed(2),
                    "ECRNumber": this.pos.get_order().uid,
                    "PrintSettings": this.payment_method.geidea_print_settings,
                    "AppId": this.payment_method.geidea_app_id
                };
                console.log('Sending Geidea payment request:', JSON.stringify(paymentRequest, null, 2));
                this.terminal.send(JSON.stringify(paymentRequest));
            });
        },

        _updatePaymentLine(line, result) {
            console.log('Updating payment line with approved result:', JSON.stringify(result, null, 2));
            
            line.card_number = result.PrimaryAccountNumber;
            line.rrn = result.RetrievalReferenceNumber;
            line.transaction_id = result.TransactionAuthCode;
            line.terminal_id = result.CardAcceptorTerminalId;
            line.card_type = result.CardNameEnglish;
            line.transaction_response = result.TransactionResponseEnglish;
            line.transaction_type = result.TransactionTypeAsReadable;
            line.transaction_date = result.TransactionDateTime;
            line.pos_entry_mode = result.POSEntryMode;
            
            // Set status to done only for this specific line
            line.set_payment_status('done');
            this.status = 'done';
            
            console.log('Payment line updated successfully, status set to done',JSON.stringify(line, null, 2));
        },

        _handleError(error) {
            console.error("geidea :Communication failed with geidea payment terminal,check the terminal connected to Com Port", error);
            Gui.showPopup('ErrorPopup', {
                title: _t('Payment Error'),
                body: _t(error.message || 'Communication failed with payment terminal')
            });
        },

        _cleanup() {
            return new Promise((resolve) => {
                if (this.terminal) {
                    console.log("Cleaning up terminal connection, current status:", this.status);
                    
                    // Clear all event handlers to prevent stale responses
                    this.terminal.onmessage = null;
                    this.terminal.onerror = null;
                    
                    // Send disconnect command before closing
                    if (this.terminal.readyState === WebSocket.OPEN) {
                        this.terminal.send(JSON.stringify({
                            "Event": "CONNECTION",
                            "Operation": "DISCONNECT"
                        }));
                    }

                    // Add event listener for close
                    this.terminal.onclose = () => {
                        this.terminal = null;
                        console.log("Terminal connection closed and cleaned up");
                        resolve();
                    };

                    // Close the connection
                    this.terminal.close();
                    
                    // Fallback timeout in case close event doesn't fire
                    setTimeout(() => {
                        if (this.terminal) {
                            console.log("Force closing terminal connection");
                            this.terminal = null;
                        }
                        resolve();
                    }, 1000);
                } else {
                    console.log("No terminal connection to cleanup");
                    resolve();
                }
            });
        },

        get paymentLineStatus() {
            return this.status;
        },
        
        // Complete reset method for new orders/payment attempts
        resetInterface() {
            console.log('Resetting Geidea payment interface, previous status:', this.status);
            this.status = 'pending';
            
            // Force cleanup any existing connections
            if (this.terminal) {
                try {
                    if (this.terminal.readyState === WebSocket.OPEN) {
                        this.terminal.send(JSON.stringify({
                            "Event": "CONNECTION",
                            "Operation": "DISCONNECT"
                        }));
                    }
                    this.terminal.close();
                } catch (error) {
                    console.warn('Error during force cleanup:', error);
                }
                this.terminal = null;
            }
            
            console.log('Geidea payment interface reset complete');
        },

        _getConnectionData() {
            const baseData = {
                "Event": "CONNECTION",
                "Operation": "CONNECT",
                "ConnectionMode": this.payment_method.geidea_connection_mode
            };

            if (this.payment_method.geidea_connection_mode === 'COM') {
                return {
                    ...baseData,
                    "ComName": this.payment_method.geidea_com_name,
                    "BaudRate": this.payment_method.geidea_baud_rate,
                    "DataBits": this.payment_method.geidea_data_bits,
                    "Parity": this.payment_method.geidea_parity
                };
            }

            return {
                ...baseData,
                "IpAddress": this.payment_method.geidea_ip_address,
                "Port": this.payment_method.geidea_port
            };
        }
    });

    return GeideaPaymentInterface;
});