/**
 * Sample JavaScript file for testing AI documentation generation
 */

class PaymentProcessor {
    constructor(apiKey, environment = 'sandbox') {
        this.apiKey = apiKey;
        this.environment = environment;
        this.baseUrl = environment === 'production' 
            ? 'https://api.payment.com' 
            : 'https://sandbox.payment.com';
    }

    /**
     * Process a payment transaction
     * @param {Object} paymentData - Payment information
     * @param {number} paymentData.amount - Amount to charge
     * @param {string} paymentData.currency - Currency code (e.g., 'USD')
     * @param {string} paymentData.cardToken - Tokenized card information
     * @returns {Promise<Object>} Payment result
     */
    async processPayment(paymentData) {
        try {
            const response = await fetch(`${this.baseUrl}/payments`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(paymentData)
            });

            if (!response.ok) {
                throw new Error(`Payment failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Payment processing error:', error);
            throw error;
        }
    }

    /**
     * Validate payment data before processing
     * @param {Object} paymentData - Payment data to validate
     * @returns {boolean} True if valid
     */
    validatePaymentData(paymentData) {
        if (!paymentData.amount || paymentData.amount <= 0) {
            return false;
        }
        if (!paymentData.currency || paymentData.currency.length !== 3) {
            return false;
        }
        if (!paymentData.cardToken) {
            return false;
        }
        return true;
    }
}

module.exports = PaymentProcessor;