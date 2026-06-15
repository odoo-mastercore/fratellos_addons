import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { roundCurrency, formatCurrency } from "@point_of_sale/app/models/utils/currency";
import { patch } from "@web/core/utils/patch";

patch(PosOrderline.prototype, {
    setup(vals) {
        super.setup(vals);
    },
    set_discount(discount, limit = 0) {
        const parsed_discount =
            typeof discount === "number"
                ? discount
                : isNaN(parseFloat(discount))
                ? 0
                : parseFloat("" + discount);
        const disc = Math.min(Math.max(parsed_discount || 0, limit), 100);
        this.discount = disc;
        if (this.order_id != undefined){
            this.order_id.recomputeOrderData();   
        }
        this.setDirty();
    }
});