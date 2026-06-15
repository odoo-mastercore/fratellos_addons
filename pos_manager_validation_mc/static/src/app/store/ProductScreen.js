import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
let check_discount_app = true;
let check_price_change = true;

patch(ProductScreen.prototype, {
    async onNumpadClick(buttonValue) {
        const order = this.pos.get_order();
        let config = this.pos.config;
        let result = true;
        if(config.discount_app && check_discount_app && buttonValue == 'discount'){
            result = await this.pos.checkPswd('discount_app', false, (order.get_orderlines().length > 0 ? order.get_selected_orderline().product_id.id : false), false, false, (order.get_partner() != undefined ? order.get_partner().id : false));
        }
        if(config.price_change && check_price_change && buttonValue == 'price'){
            result = await this.pos.checkPswd('price_change', false, (order.get_orderlines().length > 0 ? order.get_selected_orderline().product_id.id : false), false, false, (order.get_partner() != undefined ? order.get_partner().id : false));
        }
        if(result){
           super.onNumpadClick(buttonValue);
        }
    }
});