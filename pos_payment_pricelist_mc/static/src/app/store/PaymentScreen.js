import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { DatePickerPopup } from "@point_of_sale/app/utils/date_picker_popup/date_picker_popup";
import { ConnectionLostError, RPCError } from "@web/core/network/rpc";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Numpad, enhancedButtons } from "@point_of_sale/app/generic_components/numpad/numpad";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";

patch(PaymentScreen.prototype, {
    setup(vals) {
        super.setup(vals);
    },
    async addNewPaymentLine(paymentMethod) {
        if ((this.currentOrder.pricelist_id == undefined) || (this.currentOrder.pricelist_id != undefined && this.currentOrder.pricelist_id.enable_payment_exclusive_currency != true)){
            var res = await super.addNewPaymentLine(paymentMethod);
            return res;
        }else{
            var currency_idx = (paymentMethod.currency_idx != 0 ? paymentMethod.currency_idx : this.pos.company.currency_id.id);
            if (currency_idx == this.currentOrder.pricelist_id.currency_id.id && (paymentMethod.journal_idx != 0 && paymentMethod.disabled_exclusive_currency_in_pricelist != true)){
                var res = await super.addNewPaymentLine(paymentMethod);
                return res;    
            }else{
                this.dialog.add(AlertDialog, {
                    title: _t('Metodo de pago no permitido'),
                    body: _t('El metodo de pago seleccionado no esta disponible para la lista de precio ' + this.currentOrder.pricelist_id.name + '.'),
                });
                return false;
            }
        }
    },
})