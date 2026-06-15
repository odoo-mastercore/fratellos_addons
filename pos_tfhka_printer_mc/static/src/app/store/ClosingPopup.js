import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";
import { ConnectionLostError } from "@web/core/network/rpc";
import { deduceUrl } from "@point_of_sale/utils";
import { _t } from "@web/core/l10n/translation";
import { useErrorHandlers, useTrackedAsync } from "@point_of_sale/app/utils/hooks";
import { registry } from "@web/core/registry";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { useState, Component, onMounted } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(ClosePosPopup.prototype, {
    setup() {
        super.setup();
        this.generateReportFiscal = useTrackedAsync(() => this.pos.generateReportFiscal());
        //console.log('ClosePosPopup-setup-this: ', this);
        //console.log("ClosePosPopup extendido - props:", this.props);
    },
    async generateReportFiscalClosing(typeReport) {
        if (this.lock) {
            return;
        }
        this.lock = true;
        try {
            this.pos.config.typeReport = typeReport;
            await this.generateReportFiscal.call();
            this.pos.config.typeReport = undefined;
        } finally {
            this.lock = false;
        }
    }
});