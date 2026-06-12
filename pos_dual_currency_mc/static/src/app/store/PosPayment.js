import { PosPayment } from "@point_of_sale/app/models/pos_payment";
import { roundDecimals } from "@web/core/utils/numbers";
import { patch } from "@web/core/utils/patch";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";

patch(PosPayment.prototype, {
    setup(vals) {
        super.setup(vals);
        /*if (this.payment_method_id.enable_currencies == false && this.amount_foreign == undefined){
            this.amount_foreign = roundPrecision((vals.amount * this.payment_method_id.currency_rate), 0.010000) || 0;
        }*/
        //console.log('PosPayment-setup-vals: ', vals);
        //console.log('PosPayment-setup-this: ', this);
    },
    set_amount_foreign(value) {
        if (this.payment_method_id.enable_currencies){
            this.pos_order_id.assert_editable();
            this.update({
                amount_foreign: roundDecimals(
                    parseFloat(value) || 0,
                    this.payment_method_id.currency_decimal_places
                ),
            });   
        }
    },
    get_amount_foreign() {
        return this.amount_foreign || 0;
    },
    get_payment_method_currency_id() {
        return this.payment_method_id.currency_idx;
    },
    set_currency_rate_foreign(value) {
        this.currency_rate_foreign = value;
    },
    get_currency_rate_foreign() {
        return this.currency_rate_foreign;
    },
    set_currency_rate_foreign_refund(value) {
        this.currency_rate_foreign_refund = value;
    },
    get_currency_rate_foreign_refund() {
        return this.currency_rate_foreign_refund;
    },
    set_payment_reference(value) {
        this.payment_reference = value;
    },
    get_payment_reference() {
        return this.payment_reference;
    },
    set_payment_lot(value) {
        this.payment_lot = value;
    },
    get_payment_lot() {
        return this.payment_lot;
    },
    set_payment_terminal(value) {
        this.payment_terminal = value;
    },
    get_payment_terminal() {
        return this.payment_terminal;
    },
    export_for_printing() {
        var res = super.export_for_printing();
        res.amount_foreign = this.get_amount_foreign();
        res.payment_method_currency_id = this.get_payment_method_currency_id();
        res.currency_rate_foreign = this.get_currency_rate_foreign();
        return res;
    }
});