import { PaymentMethodBreakdown } from "@point_of_sale/app/components/payment_method_breakdown/payment_method_breakdown";
import { patch } from "@web/core/utils/patch";

patch(PaymentMethodBreakdown.prototype, {
    setup() {
        super.setup();
    }
});
PaymentMethodBreakdown.props.enable_currencies = { type: Boolean, optional: true };
PaymentMethodBreakdown.props.currency_format_id = { type: Number, optional: true };