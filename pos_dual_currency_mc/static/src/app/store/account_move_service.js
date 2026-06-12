import { AccountMoveService } from "@account/services/account_move_service";
import { isIosApp, isIOS } from "@web/core/browser/feature_detection";
import { patch } from "@web/core/utils/patch";

patch(AccountMoveService.prototype, {
    async downloadPdf(accountMoveId) {
        if (!this.env.services.pos.config.disabled_print_invoice){
            return super.downloadPdf(accountMoveId);
        }else{
            return;
        }
    },
});