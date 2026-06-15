import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";
import { ConnectionLostError } from "@web/core/network/rpc";
import { deduceUrl } from "@point_of_sale/utils";
let check_move_in_out_cash = true;

patch(ClosePosPopup.prototype, {
    async cashMove() {
        let config = this.pos.config;
        let result = true;
        if(config.move_in_out_cash && check_move_in_out_cash){
            result = await this.pos.checkPswd('move_in_out_cash', false, false, false, false, false);
        }
        if(result){
           await super.cashMove();
        }    
    }
});