import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useErrorHandlers, useTrackedAsync } from "@point_of_sale/app/utils/hooks";
import { registry } from "@web/core/registry";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { useState, Component, onMounted } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        //this.printReceipt = this.pos.printReceipt();
        this.printReceiptFiscal = useTrackedAsync(() => this.pos.printReceiptFiscal());
        //console.log('ReceiptScreen-this: ', this);
        if (this.pos.config.printing_invoice_automatic == true && this.pos.config.is_tax_box == true && this.currentOrder.lines.length > 0){
            setTimeout(() => {
              document.querySelector(".print-receipt-fiscal").click();
            }, 1000);
        }
    },
    orderDone() {
        if ((this.currentOrder._printed_ready == true && this.pos.config.block_new_order_if_not_been_issued_invoice == true) || (this.pos.config.block_new_order_if_not_been_issued_invoice == false)){
            super.orderDone();
        }else if (this.currentOrder.lines.length == 0){
            super.orderDone();
        }
    },
    get isPaymentContributions() {       
        return (this.currentOrder.lines.length == 0 ? true : false);
    }
})