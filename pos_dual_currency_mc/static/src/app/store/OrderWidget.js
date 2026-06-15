import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { Component, useEffect, useRef } from "@odoo/owl";
import { CenteredIcon } from "@point_of_sale/app/generic_components/centered_icon/centered_icon";
import { _t } from "@web/core/l10n/translation";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { formatMonetary } from "@web/views/fields/formatters";
import { patch } from "@web/core/utils/patch";

patch(OrderWidget.prototype, {
    setup() {
        super.setup();
        this.props.show_currency_id = this.env.services.pos.config.show_currency_id;
        this.props.show_currency_rate = this.env.services.pos.config.show_currency_rate;
    },
    get showQtyProduct() {
        var showQtyProduct = false;
        if (this.taxTotals != undefined){
            if (this.props.lines.length > 0){
                showQtyProduct = this.props.lines[0].order_id.config_id.view_quantity_products;
            }  
        }
        return showQtyProduct;
    },
    get qtyProduct() {
        var qtyProduct = 0;
        for (var i = 0; i < this.props.lines.length; i++){
            if (this.props.lines[i].product_id.to_weight){
                qtyProduct = qtyProduct + 1;
            }else{
                qtyProduct = qtyProduct + this.props.lines[i].qty;
            }
        }
        return qtyProduct;
    }
});