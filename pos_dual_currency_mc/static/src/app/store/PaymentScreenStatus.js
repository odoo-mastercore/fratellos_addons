import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreenStatus.prototype, {
    setup() {
        super.setup();
    },
    get changeTextForeign() {
        return this.env.utils.formatCurrencyForeign(this.props.order.get_change_foreign(), this.props.order.config_id.show_currency_id);
    },
    get remainingTextForeign() {
        return this.env.utils.formatCurrencyForeign(this.props.order.get_due_foreign(), this.props.order.config_id.show_currency_id);
    }
});