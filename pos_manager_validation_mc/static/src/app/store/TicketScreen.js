import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
let check_refund = true;2

patch(TicketScreen.prototype, {
    setup() {
        super.setup();
    },
    async onDoRefund() {
        const order = this.getSelectedOrder();
        let config = this.pos.config;
        let result = true;
        if(config.return_orders && check_refund){
            result = await this.pos.checkPswd('return_orders', false, false, false, order.id, (order.get_partner() != undefined ? order.get_partner().id : false));
        }
        if(result){
           await super.onDoRefund();
        }
    }
}); 