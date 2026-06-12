import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(vals);
        this.show_currency_id = this.config.show_currency_id;
        this.show_currency_rate = this.config.show_currency_rate;
        //console.log('PosOrder-setup-this: ', this);
    },
});