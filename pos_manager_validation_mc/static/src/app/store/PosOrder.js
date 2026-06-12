import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
let check_order_line_delete = true;

patch(PosOrder.prototype, {
    async removeOrderline(line) {
        const order = this;
        let config = this.config;
        let result = true;
        if(config.order_line_delete && check_order_line_delete){
            result = await this.pos.checkPswd('order_line_delete', false, line.product_id.id, false, false, (order.get_partner() != undefined ? order.get_partner().id : false));
        }
        if(result){
           await super.removeOrderline(line);
        }
    }
});