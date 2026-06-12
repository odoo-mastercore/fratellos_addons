import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { roundCurrency, formatCurrency } from "@point_of_sale/app/models/utils/currency";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PosOrderline.prototype, {
    setup(vals) {
        super.setup(vals);
    },
    get currency_foreign() {
        var currency = {};
        currency.id = this.config.show_currency_id;
        currency.decimal_places = this.config.show_currency_decimal_places;
        currency.position = this.config.show_currency_position;
        currency.rounding = this.config.show_currency_rounding;
        currency.symbol = this.config.show_currency_symbol;
        if (this.order_id.currency_rate_foreign_refund != undefined){
            currency.rate = this.order_id.currency_rate_foreign_refund;
        }else if (this.order_id.currency_rate_foreign != undefined){
            currency.rate = this.order_id.currency_rate_foreign;    
        }else{
            currency.rate = this.config.show_currency_rate;
        }
        return currency;
    },
    getPriceForeignString() {
        var currency = {};
        currency.id = this.config.show_currency_id;
        return this.get_discount_str() === "100"
            ? // free if the discount is 100
              _t("Free")
            : this.combo_line_ids.length > 0
            ? // empty string if it is a combo parent line
              ""
            : formatCurrency((this.get_display_price() * this.currency_foreign.rate), this.currency_foreign);
    },
    getDisplayData() {
        var res = super.getDisplayData();
        res.price_foreign = this.getPriceForeignString();
        res.unitPrice_foreign = formatCurrency((this.get_unit_display_price() * this.currency_foreign.rate), this.currency_foreign);
        res.price_unit_foreign = roundCurrency((this.get_unit_display_price() * this.currency_foreign.rate), this.currency_foreign);
        //console.log('getDisplayData-res: ', res);
        //console.log('getDisplayData-currency_foreign: ', this.currency_foreign);
        return res;
    },
    setLinePrice() {
        const prices = this.get_all_prices();
        //console.log('setLinePrice-this: ', this);
        //console.log('setLinePrice-prices: ', prices);
        super.setLinePrice();
        this.price_unit_foreign = roundCurrency((this.get_unit_display_price() * this.currency_foreign.rate), this.currency_foreign);
        this.price_subtotal_foreign = roundCurrency((prices.priceWithoutTax * this.currency_foreign.rate), this.currency_foreign);
        this.price_subtotal_incl_foreign = roundCurrency((prices.priceWithTax * this.currency_foreign.rate), this.currency_foreign);
        //console.log('setLinePrice-this(F): ', this);
    }
});