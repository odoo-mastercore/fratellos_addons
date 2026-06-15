import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype, {
    setup() {
        super.setup();
    }
});
Orderline.props.line.shape.price_foreign = { type: String, optional: true };
Orderline.props.line.shape.unitPrice_foreign = { type: String, optional: true };
Orderline.props.line.shape.price_unit_foreign = { type: Number, optional: true };