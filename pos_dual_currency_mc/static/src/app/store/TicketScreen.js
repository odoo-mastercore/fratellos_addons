import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";

patch(TicketScreen.prototype, {
    setup() {
        super.setup();
    },
    async onDoRefund() {
        await super.onDoRefund();
        this.pos.get_order().currency_rate_foreign_refund = this.getSelectedOrder().currency_rate_foreign;
        for (var i = 0; i < this.pos.config.payment_method_ids.length; i++){
            var rate_refund = false;
            var currency_rate_refund = 0.0;
            for (var x = 0; x < this.getSelectedOrder().payment_ids.length; x++){
                if (this.pos.config.payment_method_ids[i].currency_idx == this.getSelectedOrder().payment_ids[x].payment_method_id.currency_idx){
                    rate_refund = true;
                    currency_rate_refund = this.getSelectedOrder().payment_ids[x].currency_rate_foreign;
                }
            }
            if (rate_refund == true){
                this.pos.config.payment_method_ids[i].currency_rate_refund = currency_rate_refund;
            }else{
                this.pos.config.payment_method_ids[i].currency_rate_refund = undefined;
            }
        }
        this.pos.get_order().to_refund = this.getHasItemsToRefund();
        //this.pos.get_order().setup({});
        console.log('onDoRefund-get_order: ', this.pos.get_order());
        //console.log('onDoRefund-getHasItemsToRefund: ', this.getHasItemsToRefund());
        
    }
});