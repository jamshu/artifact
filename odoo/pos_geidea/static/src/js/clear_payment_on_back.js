/** @odoo-module **/
import PaymentScreen from 'point_of_sale.PaymentScreen';
import ProductScreen from 'point_of_sale.ProductScreen';
import Registries from 'point_of_sale.Registries';

const ClearPaymentsProductScreen = (ProductScreen) =>
    class extends ProductScreen {
        mounted() {
            super.mounted();
            const order = this.env.pos.get_order();
                if (order && order.paymentlines.length) {
                    order.paymentlines.slice().forEach((pl) => {
                        order.remove_paymentline(pl);

                    });
                }
       }
    };

Registries.Component.extend(PaymentScreen, ClearPaymentsProductScreen);