import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { DatePickerPopup } from "@point_of_sale/app/utils/date_picker_popup/date_picker_popup";
import { ConnectionLostError, RPCError } from "@web/core/network/rpc";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Numpad, enhancedButtons } from "@point_of_sale/app/generic_components/numpad/numpad";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";
import { ask, makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    setup(vals) {
        super.setup(vals);
        setTimeout(() => {
            if (this.pos.config.forced_button_invoice){
                this.toggleIsToInvoice();
            }
        }, 1000);
    },
    async addNewPaymentLine(paymentMethod) {
        console.log('PaymentScreen-addNewPaymentLine-this: ', this);
        var res = await super.addNewPaymentLine(paymentMethod);
        console.log('PaymentScreen-addNewPaymentLine-res: ', res);
        var buttons = [];
        if (this.pos.config.enable_popup_references_payment){
            if (paymentMethod.enable_payment_lot){
                var payment_lot = await makeAwaitable(this.dialog, TextInputPopup, {
                    title:  _t("Ingrese los datos del lote"),
                    buttons,
                    rows: 1,
                    startingValue: '',
                });
                while (payment_lot == undefined) {
                     payment_lot = await makeAwaitable(this.dialog, TextInputPopup, {
                        title:  _t("Ingrese los datos del lote"),
                        buttons,
                        rows: 1,
                        startingValue: '',
                    });   
                }
                this.selectedPaymentLine.set_payment_lot(payment_lot);
            }
            if (paymentMethod.enable_payment_reference){
                var payment_reference = await makeAwaitable(this.dialog, TextInputPopup, {
                    title:  _t("Ingrese los datos de la referencia"),
                    buttons,
                    rows: 1,
                    startingValue: '',
                });
                while (payment_reference == undefined) {
                    payment_reference = await makeAwaitable(this.dialog, TextInputPopup, {
                        title:  _t("Ingrese los datos de la referencia"),
                        buttons,
                        rows: 1,
                        startingValue: '',
                    });
                }
                this.selectedPaymentLine.set_payment_reference(payment_reference);
            }
            if (paymentMethod.enable_payment_terminal){
                var payment_terminal = await makeAwaitable(this.dialog, TextInputPopup, {
                    title:  _t("Ingrese los datos del terminal"),
                    buttons,
                    rows: 1,
                    startingValue: '',
                });
                while (payment_terminal == undefined) {
                    payment_terminal = await makeAwaitable(this.dialog, TextInputPopup, {
                        title:  _t("Ingrese los datos del terminal"),
                        buttons,
                        rows: 1,
                        startingValue: '',
                    });
                }
                this.selectedPaymentLine.set_payment_terminal(payment_terminal);
            }   
        }
        console.log('addNewPaymentLine-selectedPaymentLine', this.selectedPaymentLine);
        return res;
    },
    updateSelectedPaymentline(amount = false) {
        this.numberBufferTemp = this.numberBuffer.get();
        if (this.selectedPaymentLine != undefined && this.selectedPaymentLine.payment_method_id.enable_currencies){
            if (amount === false) {
                if (this.numberBuffer.get() === null) {
                    amount = null;
                } else if (this.numberBuffer.get() === "") {
                    amount = 0;
                } else {
                    amount = this.numberBuffer.getFloat();
                }
                var currency_rate = 0.0;
                if (this.currentOrder.to_refund != undefined && this.selectedPaymentLine.payment_method_id.currency_rate_refund != undefined){
                    currency_rate = this.selectedPaymentLine.payment_method_id.currency_rate_refund;
                }else{
                    currency_rate = this.selectedPaymentLine.payment_method_id.currency_rate;
                }
                var am = roundPrecision((amount * (1 / currency_rate)), this.selectedPaymentLine.payment_method_id.currency_rounding);
                var currentOrder = this.currentOrder;
                var total_payment = 0.0;
                for (var i = 0; i < this.currentOrder.payment_ids.length; i++){
                    if ( this.currentOrder.payment_ids[i].uuid != this.selectedPaymentLine.uuid){
                        total_payment = total_payment + this.currentOrder.payment_ids[i].get_amount();
                    }
                }
                total_payment = roundPrecision(total_payment, this.pos.currency.rounding);
                if (this.currentOrder.to_refund == undefined){
                    if (this.currentOrder.get_change() > 0 && total_payment > this.currentOrder.get_total_with_tax()){
                        amount = amount * (-1);
                        am = am * (-1);
                    }  
                }else{
                    if (this.currentOrder.get_total_with_tax() < 0.0 && total_payment > this.currentOrder.get_total_with_tax()){ //total_payment == 0 && this.currentOrder.get_change() == 0 && 
                        amount = amount * (-1);
                        am = am * (-1);
                    }   
                }
                this.selectedPaymentLine.set_amount_foreign(amount);
                this.selectedPaymentLine.set_amount(am);
            }
        }else{
            super.updateSelectedPaymentline(amount);
            if (this.selectedPaymentLine != undefined){
                var total_payment = 0.0;
                for (var i = 0; i < this.currentOrder.payment_ids.length; i++){
                    if ( this.currentOrder.payment_ids[i].uuid != this.selectedPaymentLine.uuid){
                        total_payment = total_payment + this.currentOrder.payment_ids[i].get_amount();
                    }
                }
                total_payment = roundPrecision(total_payment, this.pos.currency.rounding);
                if (this.numberBuffer.get() === null) {
                    amount = null;
                } else if (this.numberBuffer.get() === "") {
                    amount = 0;
                } else {
                    amount = this.numberBuffer.getFloat();
                }
                if (this.currentOrder.to_refund == undefined){
                    if (this.currentOrder.get_change() > 0 && total_payment > this.currentOrder.get_total_with_tax()){
                        amount = amount * (-1);
                    }   
                }else{
                    if (this.currentOrder.get_total_with_tax() < 0.0 && total_payment > this.currentOrder.get_total_with_tax()){ //total_payment == 0 && this.currentOrder.get_change() == 0 && 
                        amount = amount * (-1);
                    }
                }
                this.selectedPaymentLine.set_amount(amount);   
            }
        }
    },
    showMaxValueError() {
        //this.numberBuffer.set(this.currentOrder.get_due().toString().replace('.',','));
        this.numberBuffer.set(this.numberBufferTemp.toString().replace('.',','));
        /*this.dialog.add(AlertDialog, {
            title: _t("Maximum value reached"),
            body: _t(
                "The amount cannot be higher than the due amount if you don't have a cash payment method configured."
            ),
        });*/
    }
})