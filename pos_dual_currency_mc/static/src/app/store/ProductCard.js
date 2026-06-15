import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";
import { Component, useEffect, useState } from "@odoo/owl";
import { debounce } from "@web/core/utils/timing";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useTrackedAsync } from "@point_of_sale/app/utils/hooks";
import { useService } from "@web/core/utils/hooks";
import { AccordionItem } from "@point_of_sale/app/generic_components/accordion_item/accordion_item";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";

patch(ProductCard.prototype, {
    async setup(){
        super.setup();
        /*console.log('ProductCard-this: ', this);
        console.log('ProductCard-product: ', this.props.product);
        console.log('ProductCard-env: ', this.env);
        console.log('ProductCard-services: ', this.env.services);
        console.log('ProductCard-pos: ', this.env.services.pos);
        console.log('ProductCard-get_order: ', this.env.services.pos.get_order());
        this.fetchStock = useTrackedAsync((p) => this.env.services.pos.getProductInfo(p, 1), { keepLast: true });
        const debouncedFetchStocks = debounce(async (product) => {
            let result = {};
            if (!this.props.info) {
                await this.fetchStock.call(product);
                if (this.fetchStock.status === "error") {
                    throw this.fetchStock.result;
                }
                result = this.fetchStock.result;
            } else {
                result = this.props.info;
            }
            if (result) {
                const productInfo = result.productInfo;
                this.props.product.price_with_tax = productInfo.all_prices.price_with_tax;
                this.props.product.price_without_tax = productInfo.all_prices.price_without_tax;
                this.props.product.tax_name = productInfo.all_prices.tax_details[0]?.name || "";
                this.props.product.tax_amount = productInfo.all_prices.tax_details[0]?.amount || 0;
            }
        }, 500);
        useEffect(
            () => {
                debouncedFetchStocks(this.props.product);
            },
            () => [this.props.product]
        );*/
    },
    productPrice() {
        /*if (this.env.services.pos.config.iface_tax_included === "total") {
            return this.env.utils.formatCurrency(this.props.product.price_with_tax || 1);
        } else {
            return this.env.utils.formatCurrency(this.props.product.price_without_tax || 1);
        }*/
        if (this.env.services.pos.config.iface_tax_included === "total" && this.props.product.taxes_id.length > 0) {
            return this.env.utils.formatCurrency((this.props.product.get_price(this.env.services.pos.get_order().pricelist_id, 1) * (1 + (this.props.product.taxes_id[0].amount / 100))) || 1);
        }else{
            return this.env.utils.formatCurrency(this.props.product.get_price(this.env.services.pos.get_order().pricelist_id, 1) || 1);
        }
    },
    productPriceForeign() {
        /*if (this.env.services.pos.config.iface_tax_included === "total") {
            return this.env.utils.formatCurrencyForeign((this.props.product.price_with_tax || 1) * this.env.services.pos.config.show_currency_rate, this.env.services.pos.config.show_currency_id);
        } else {
            return this.env.utils.formatCurrencyForeign((this.props.product.price_without_tax || 1) * this.env.services.pos.config.show_currency_rate, this.env.services.pos.config.show_currency_id);
        }*/
        if (this.env.services.pos.config.iface_tax_included === "total" && this.props.product.taxes_id.length > 0) {
            return this.env.utils.formatCurrencyForeign((roundPrecision((this.props.product.get_price(this.env.services.pos.get_order().pricelist_id, 1) * (1 + (this.props.product.taxes_id[0].amount / 100))), 0.010000) * this.env.services.pos.config.show_currency_rate), this.env.services.pos.config.show_currency_id);
        }else{
            return this.env.utils.formatCurrencyForeign((this.props.product.get_price(this.env.services.pos.get_order().pricelist_id, 1) * this.env.services.pos.config.show_currency_rate), this.env.services.pos.config.show_currency_id);
        }
    }
});