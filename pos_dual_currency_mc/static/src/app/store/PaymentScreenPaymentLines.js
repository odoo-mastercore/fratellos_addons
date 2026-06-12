import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { patch } from "@web/core/utils/patch";
import { ask, makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreenPaymentLines.prototype, {
    setup() {
        super.setup();
    },
    async setPaymentInfo(paymentline, type) {
        console.log('setPaymentInfo-this: ', this);
        console.log('setPaymentInfo-paymentline: ', paymentline);
        console.log('setPaymentInfo-type: ', type);
        console.log('setPaymentInfo-selectLine: ', this.props.selectLine(paymentline.uuid));
        var title; '';
        if (type == 'payment_lot'){
            title = 'Ingrese los datos del lote';
        }else if(type == 'payment_reference'){
            title = 'Ingrese los datos de la referencia';
        }else{
            title = 'Ingrese los datos del terminal';
        }
        var buttons = [];
        var payment_info = await makeAwaitable(this.dialog, TextInputPopup, {
            title:  _t(title),
            buttons,
            rows: 1,
            startingValue: '',
        });
        while (payment_info == undefined) {
             payment_info = await makeAwaitable(this.dialog, TextInputPopup, {
                title:  _t(title),
                buttons,
                rows: 1,
                startingValue: '',
            });
        }
        if (type == 'payment_lot'){
            paymentline.set_payment_lot(payment_info);
        }else if(type == 'payment_reference'){
            paymentline.set_payment_reference(payment_info);
        }else{
            paymentline.set_payment_terminal(payment_info);
        }
    }
});