import { InvoiceButton } from "@point_of_sale/app/screens/ticket_screen/invoice_button/invoice_button";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useErrorHandlers, useTrackedAsync } from "@point_of_sale/app/utils/hooks";
import { registry } from "@web/core/registry";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { useState, Component, onMounted } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(InvoiceButton.prototype, {
    setup() {
        super.setup();
        this.printReceiptFiscal = useTrackedAsync(() => this.pos.printReceiptFiscal());
        this.reprintReceiptFiscal = useTrackedAsync(() => this.pos.reprintReceiptFiscal());
        //console.log('InvoiceButton-this: ', this);
    },
    get commandName() {
        if (this.pos.config.is_tax_box){
            if (this.props.order.fiscal_invoice_number != false && this.props.order.fiscal_invoice_number != '') {
                return _t("Reprint Invoice");
            } else {
                return _t("Generar Factura");
            }   
        }else{
            return super.commandName;
        }
    },
    async generateOrder() {
        //console.log('InvoiceButton-generateOrder-this: ', this);
        if (this.lock) {
            return;
        }
        this.lock = true;
        try {
            const order = this.props.order;
            const originOrder = this.pos.get_order();
            //console.log('InvoiceButton-generateOrder-order: ', order);
            if (!order) {
                return;
            }
            this.pos.set_order(order);
            if (order.fiscal_invoice_number != false){
                await this.reprintReceiptFiscal.call();
            }else{
                await this.printReceiptFiscal.call();
            }
            //this.pos.add_new_order();
            this.pos.set_order(originOrder);
            setTimeout(() => {
                this.pos.data.read("pos.order", [order.id]);
            }, 2000);
            
        } finally {
            this.lock = false;
        }
    }
})