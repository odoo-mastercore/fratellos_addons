import { _t } from "@web/core/l10n/translation";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";
//import { usePopup } from "@odoo/owl";
//const { showPopup } = usePopup();

patch(PosStore.prototype, {
    async settleCustomerDue(partner) {
        const updatedDue = await this.refreshTotalDueOfPartner(partner);
        const totalDue = updatedDue ? updatedDue[0].total_due : partner.total_due;
        const paymentMethods = this.config.payment_method_ids.filter(
            (method) => method.type != "pay_later"
        );
        const selectionList = paymentMethods.map((paymentMethod) => ({
            id: paymentMethod.id,
            label: paymentMethod.name,
            item: paymentMethod,
        }));
        this.dialog.add(SelectionPopup, {
            title: _t("Seleccione el método de pago para saldar la deuda"),
            list: selectionList,
            getPayload: (selectedPaymentMethod) => {
                // Reuse an empty order that has no partner or has partner equal to the selected partner.
                let newOrder;
                const emptyOrder = this.get_open_orders().find(
                    (order) =>
                        order.lines.length === 0 &&
                        order.payment_ids.length === 0 &&
                        (!order.partner || order.partner.id === partner.id)
                );
                if (emptyOrder) {
                    newOrder = emptyOrder;
                    // Set the empty order as the current order.
                    this.set_order(newOrder);
                } else {
                    newOrder = this.add_new_order();
                }
                const payment = newOrder.add_paymentline(selectedPaymentMethod);
                newOrder.is_settling_account = true;
                payment.set_amount(totalDue);
                if (payment.payment_method_id.enable_currencies){
                    payment.set_amount_foreign(roundPrecision((totalDue * payment.payment_method_id.currency_rate), payment.payment_method_id.currency_rounding));
                }
                newOrder.set_partner(partner);
                this.showScreen("PaymentScreen", { orderUuid: this.selectedOrderUuid });
            },
        });
    }
});