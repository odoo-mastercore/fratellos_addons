import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(vals);
        this.show_currency_id = this.config.show_currency_id;
        this.show_currency_rate = this.config.show_currency_rate;
        //console.log('PosOrder-setup-this: ', this);
    },
    get taxTotals() {
        var res = super.taxTotals;
        //console.log('PosOrder-taxTotals-this: ', this);
        res.show_currency_id = this.config.show_currency_id;
        if (res.order_sign == 1){
            res.show_currency_rate = this.config.show_currency_rate;
            res.amount_total_foreign = roundPrecision((res.order_total * res.order_sign * this.config.show_currency_rate), this.config.show_currency_rounding);
            res.amount_tax_foreign = roundPrecision((res.tax_amount * res.order_sign * this.config.show_currency_rate), this.config.show_currency_rounding);
        }else{
            res.show_currency_rate = this.config.show_currency_rate;
            res.amount_total_foreign = roundPrecision((res.order_total * res.order_sign * this.currency_rate_foreign_refund), this.config.show_currency_rounding);
            res.amount_tax_foreign = roundPrecision((res.tax_amount * res.order_sign * this.currency_rate_foreign_refund), this.config.show_currency_rounding);
        }
        //console.log('taxTotals-res(F): ', res);
        return res;
    },
    get_change_foreign() {
        var res = this.get_change();
        if (this.currency_rate_foreign_refund == undefined){
            res = roundPrecision((res * this.config.show_currency_rate), this.config.show_currency_rounding);   
        }else{
            res = roundPrecision((res * this.currency_rate_foreign_refund), this.config.show_currency_rounding);
        }
        return res;
    },
    get_due_foreign() {
        var res = this.get_due();
        if (this.currency_rate_foreign_refund == undefined){
            res = roundPrecision((res * this.config.show_currency_rate), this.config.show_currency_rounding);   
        }else{
            res = roundPrecision((res * this.currency_rate_foreign_refund), this.config.show_currency_rounding);
        }
        return res;
    },
    getTotalDueForeign() {
        var res = this.getTotalDue();
        if (this.currency_rate_foreign_refund == undefined){
            res = roundPrecision((res * this.config.show_currency_rate), this.config.show_currency_rounding);   
        }else{
            res = roundPrecision((res * this.currency_rate_foreign_refund), this.config.show_currency_rounding);
        }
        return res;
    },
    add_paymentline(payment_method) {
        var res = super.add_paymentline(payment_method);
        if (this.to_refund != undefined && payment_method.currency_rate_refund != undefined){
            res.set_amount_foreign(roundPrecision((res.amount * payment_method.currency_rate_refund), payment_method.currency_rounding));
            res.set_currency_rate_foreign(payment_method.currency_rate_refund);
        }else{
            res.set_amount_foreign(roundPrecision((res.amount * payment_method.currency_rate), payment_method.currency_rounding));
            res.set_currency_rate_foreign(payment_method.currency_rate);
        }
        return res;
    },
    serialize() {
        if (this.currency_rate_foreign_refund == undefined){
            this.currency_rate_foreign = this.config.show_currency_rate;   
        }else{
            this.currency_rate_foreign = this.currency_rate_foreign_refund;
        }
        this.amount_total_foreign = roundPrecision((this.amount_total * this.currency_rate_foreign), this.config.show_currency_rounding);
        this.amount_tax_foreign = roundPrecision((this.amount_tax * this.currency_rate_foreign), this.config.show_currency_rounding);
        this.amount_paid_foreign = roundPrecision((this.amount_paid * this.currency_rate_foreign), this.config.show_currency_rounding);
        if (this.lines.length > 0){
            if (this.lines[0].price_unit_foreign == false){
                for (var i = 0; i < this.lines.length; i++){
                    this.lines[i].setLinePrice();
                }
            }
        }
        //console.log('serialize-this(F): ', this);
        return super.serialize(...arguments);;
    },
    set_to_invoice(to_invoice) {
        if (this.config_id.forced_button_invoice){
            to_invoice = true;
        }
        super.set_to_invoice(to_invoice);
    }
});