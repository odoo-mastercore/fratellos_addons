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
        var res = await super.addNewPaymentLine(paymentMethod);
        //if (this.currentOrder.get_change() == 0.0){
        if (this.currentOrder.get_total_with_tax() > 0 && paymentMethod.enable_discount == true){
            this.apply_adjustment(paymentMethod.adjustment_product_id, paymentMethod.discount_type, paymentMethod.rate_discount, 'add', paymentMethod.round_payment_amount, paymentMethod.id, undefined, paymentMethod.apply_discount_on_lines, paymentMethod.apply_total_discount_with_differences_less_than, paymentMethod.apply_discount_to_total_order);
        }
        //}
        if (this.currentOrder.get_total_with_tax() > 0.0 && this.amount_discount != 0.0 && this.amount_discount != undefined){
            var amount = 0.0;
            setTimeout(() => {
                if (this.currentOrder.get_total_with_tax() != this.currentOrder.get_total_paid()){
                    if (this.currentOrder.payment_ids.length == 1){
                        amount = this.currentOrder.get_total_with_tax();
                    }else{
                        amount = (this.amount_discount + this.selectedPaymentLine.get_amount());
                    }
                    this._updateSelectedPaymentline_for_discount(amount);
                    this.amount_discount = 0.0;
                    var line_discount = this.currentOrder.get_orderlines().filter(line => line.get_product() === paymentMethod.adjustment_product_id);
                    if (line_discount.length > 0){
                        line_discount.payment_method_uuid = this.selectedPaymentLine.uuid;
                    }
                }
            }, 500);
        }
        return res;
    },
    updateSelectedPaymentline(amount = false) {
        super.updateSelectedPaymentline(amount);
        if (this.currentOrder.get_total_with_tax() > 0.0 && this.selectedPaymentLine != undefined && this.selectedPaymentLine.payment_method_id.enable_discount == true){
            this.apply_adjustment(this.selectedPaymentLine.payment_method_id.adjustment_product_id, this.selectedPaymentLine.payment_method_id.discount_type, this.selectedPaymentLine.payment_method_id.rate_discount, 'update', this.selectedPaymentLine.payment_method_id.round_payment_amount, this.selectedPaymentLine.payment_method_id.id, this.selectedPaymentLine.uuid, this.selectedPaymentLine.payment_method_id.apply_discount_on_lines, this.selectedPaymentLine.payment_method_id.apply_total_discount_with_differences_less_than, this.selectedPaymentLine.payment_method_id.apply_discount_to_total_order);
            this.amount_discount = 0.0;
        }
    },
    deletePaymentLine(uuid) {
        const linep = this.paymentLines.find((line) => line.uuid === uuid);
        this.calculate_discount = true;
        if (this.currentOrder.get_total_with_tax() > 0.0 && this.selectedPaymentLine != undefined && linep.payment_method_id != undefined && linep.payment_method_id.enable_discount == true){
            if (linep.payment_method_id.apply_discount_on_lines == false){
                var product  = this.selectedPaymentLine.payment_method_id.adjustment_product_id;
                var lines    = this.currentOrder.get_orderlines();
                lines.filter(line => line.get_product() === product)
                        .forEach(line => this.currentOrder.removeOrderline(line));
                if (lines) {
                    lines.forEach((line) => line.set_discount(0));
                }
            }else{
                var orderlines = this.currentOrder.get_orderlines();
                if (orderlines) {
                    orderlines.forEach((line) => line.set_discount(0));
                }
            }
        }
        this.amount_discount = 0.0;
        super.deletePaymentLine(uuid);
        setTimeout(() => {
            if (this.currentOrder.get_total_with_tax() > 0.0 && this.currentOrder.payment_ids.length > 0){
                var lined = this.payment_ids != undefined ? this.payment_ids.filter(line => line.payment_method_id.enable_discount == true):[];
                if (lined.length > 0){
                    this.currentOrder.select_paymentline(lined[0]);
                    if (this.selectedPaymentLine.payment_method_id.enable_discount == true){
                        this.apply_adjustment(this.selectedPaymentLine.payment_method_id.adjustment_product_id, this.selectedPaymentLine.payment_method_id.discount_type, this.selectedPaymentLine.payment_method_id.rate_discount, 'update', this.selectedPaymentLine.payment_method_id.round_payment_amount, this.selectedPaymentLine.payment_method_id.id, this.selectedPaymentLine.uuid, this.selectedPaymentLine.payment_method_id.apply_discount_on_lines, this.selectedPaymentLine.payment_method_id.apply_total_discount_with_differences_less_than, this.selectedPaymentLine.payment_method_id.apply_discount_to_total_order);
                        this.amount_discount = 0.0;
                    }
                }
            }
        }, 1000);
    },
    _updateSelectedPaymentline_for_discount(amount) {
        if (this.paymentLines.every((line) => line.paid)) {
            this.currentOrder.add_paymentline(this.payment_methods_from_config[0]);
        }
        if (!this.selectedPaymentLine) return; // do nothing if no selected payment line
        // disable changing amount on payment_ids with running or done payments on a payment terminal
        const payment_terminal = this.selectedPaymentLine.payment_method_id.payment_terminal;
        if (
            payment_terminal &&
            !['pending', 'retry'].includes(this.selectedPaymentLine.get_payment_status())
        ) {
            return;
        }
        this.selectedPaymentLine.set_amount(amount);
        this.amount_discount = 0.0
    },
    async apply_adjustment(adjustment_product_id, type, pc, action, round_payment_amount, payment_method_id, uuid, apply_discount_on_lines, differences_less_than, apply_discount_to_total_order) {
        var self = this;
        var order    = this.currentOrder;
        var lines    = order.get_orderlines();
        const product = adjustment_product_id;
        var total_with_tax_discount = this.currentOrder.total_with_tax_discount;
        var line_discount = undefined;
        console.log('apply_adjustment-this: ', this);
        console.log('apply_adjustment-product: ', product);
        if (product === undefined) {
            this.dialog.add(AlertDialog, {
                title: _t("No se encontró ningún producto con " + (type == 'discount' ? "descuento":"recargo")),
                body: _t('El producto con ' + (type == 'discount' ? "descuento":"recargo") + ' parece estar mal configurado. Asegúrate de que esté marcado como "Vendible" y "Disponible en el punto de venta".'),
            });
            return;
        }
        // Remove existing discounts
        var discount_total = 0.0;
        if (apply_discount_on_lines == false){
            // Remove existing discounts
            line_discount = lines.filter(line => line.get_product() === product);
            lines.filter((line) => line.get_product() === product).forEach((line) => line.set_unit_price(0));
        }else{
            var orderlines = this.currentOrder.get_orderlines();
            // Remove existing discounts
            lines.forEach((line) => line.set_discount(0));
        }
        // Add one discount line per tax group
        this.amount_discount = 0.0;
        var tax_ids_array_disc;
        let discount = 0;
        var baseToDiscount = 0.0;
        for (var i = 0; i < this.pos.models["account.tax"].length; i++){
            if (tax_ids_array_disc == undefined && this.pos.models["account.tax"].amount == 0.0){
                tax_ids_array_disc = [this.pos.models["account.tax"][i].id];
            }
        }
        //console.log('payment_ids: ', order.payment_ids);
        for (var i =0; i < order.payment_ids.length; i++){
            if (order.payment_ids[i].payment_method_id.apply_discount_to_total_order == true){
                apply_discount_to_total_order = true;
                type = order.payment_ids[i].payment_method_id.discount_type;
            }
        }
        //console.log('apply_discount_to_total_order: ', apply_discount_to_total_order);
        if (apply_discount_to_total_order == true){
            baseToDiscount = roundPrecision(this.currentOrder.get_total_with_tax(), this.pos.config.show_currency_rounding);
        }else if (action == 'update'){
            baseToDiscount = this.selectedPaymentLine.amount - (order.get_change() > 0 ? order.get_change() : 0);
            var amount_payment = 0.0;
            for (var i=0; i < order.payment_ids.length; i++){
                if (order.payment_ids[i].payment_method_id.enable_discount == true && order.payment_ids[i].payment_method_id.discount_type == type && uuid != order.payment_ids[i].uuid){
                    amount_payment = amount_payment + order.payment_ids[i].amount;
                }
            }
            baseToDiscount = baseToDiscount + amount_payment;
            if ((this.selectedPaymentLine.amount + amount_payment) >= total_with_tax_discount){
                baseToDiscount = roundPrecision(this.currentOrder.get_total_with_tax(), this.pos.config.show_currency_rounding);
            }
        }else if (order.payment_ids.length > 0){
            var amount_payment = 0.0;
            for (var i=0; i < order.payment_ids.length; i++){
                if (order.payment_ids[i].payment_method_id.enable_discount == true && order.payment_ids[i].payment_method_id.discount_type == type){
                    amount_payment = amount_payment + order.payment_ids[i].amount;
                }
            }
            baseToDiscount = roundPrecision(this.currentOrder.get_total_with_tax() - this.currentOrder.get_total_paid() + amount_payment, this.pos.config.show_currency_rounding);
        }else{
            baseToDiscount = roundPrecision(this.currentOrder.get_total_with_tax(), this.pos.config.show_currency_rounding);
        }
        // We add the price as manually set to avoid recomputation when changing customer.
        if (type == "discount"){
            discount = - roundPrecision(pc / 100.0 * baseToDiscount, 0.000100);
        }else{
            discount = roundPrecision(pc / 100.0 * baseToDiscount, 0.000100);
        }
        if (order.is_second == true && type == "discount"){
            discount = 0;
        }
        if (discount != 0) {
            discount_total = roundPrecision(discount_total + discount, 0.000100);
        }
        discount_total = roundPrecision(discount_total, 0.000100);
        if (discount_total != 0) {
            this.amount_discount = roundPrecision(this.currentOrder.get_total_with_tax() - this.currentOrder.get_total_paid() + discount_total, this.pos.config.show_currency_rounding);
            if (round_payment_amount == true){
                discount_total = roundPrecision(discount_total, this.pos.config.show_currency_rounding);
                this.amount_discount = roundPrecision(this.amount_discount, 1.000000);
                var diff = 0.0;
                if (action == 'add'){
                    diff = roundPrecision((this.currentOrder.get_total_with_tax() - this.currentOrder.get_total_paid()), this.pos.config.show_currency_rounding);
                    diff = roundPrecision((diff + discount_total + (this.amount_discount > 0 ? ((-1) * this.amount_discount) : this.amount_discount)), this.pos.config.show_currency_rounding);
                }
                if (action == 'update' && (this.currentOrder.get_change() > 0.0 || this.currentOrder.get_total_paid() > total_with_tax_discount)){
                    diff = roundPrecision((this.currentOrder.get_total_with_tax() - this.currentOrder.get_total_paid()), this.pos.config.show_currency_rounding);
                    diff = diff + discount_total;
                    var change = roundPrecision(diff, 1.000000);
                    diff = roundPrecision((diff - change), this.pos.config.show_currency_rounding);
                }
                discount_total = discount_total - diff;
            }
            product.payment_method_id = payment_method_id;
            if (apply_discount_on_lines == false){
                discount_total = roundPrecision(discount_total, this.pos.config.show_currency_rounding);
                /*if (this.currentOrder.pricelist_id != undefined && this.currentOrder.pricelist_id.currency_id.id != 2){
                    differences_less_than = roundPrecision((differences_less_than * parseFloat(this.env.pos.config.show_currency_rate)), 0.000100);
                }*/
                if ((this.currentOrder.get_total_paid() + differences_less_than) >= this.currentOrder.total_with_tax_discount){
                    discount_total = this.currentOrder.discount_total;
                }
                if (line_discount.length == 0){
                    await this.pos.addLineToCurrentOrder(
                        { product_id: product, price_unit: discount_total, tax_ids: tax_ids_array_disc },
                        { merge: false }
                    );
                }else{
                    line_discount[0].set_unit_price(discount_total);
                }
            }else{
                if ((this.currentOrder.get_total_paid() + differences_less_than) >= this.currentOrder.total_with_tax_discount){
                    discount_total = this.currentOrder.discount_total;
                }
                var total_before = self.currentOrder.get_total_with_tax();
                var orderlines = self.currentOrder.get_orderlines();
                orderlines.forEach((line) => line.set_discount(0));
                var total_after = self.currentOrder.get_total_with_tax();
                if(total_after != total_before){
                    discount_total = parseFloat(discount_total) + parseFloat(( total_after - total_before).toFixed(2));
                }

                var percentage =  roundPrecision(((discount_total / roundPrecision(self.currentOrder.get_total_with_tax(), this.pos.config.show_currency_rounding)) * 100), 0.000100);
                if (percentage < 0){
                    percentage = roundPrecision((percentage * (-1)), 0.001000);
                }else{
                    percentage = roundPrecision(percentage, 0.001000);
                }
                if (type == "increase"){
                    percentage = percentage * (-1);
                }
                orderlines.forEach((line) => line.set_discount(parseFloat(percentage), (percentage < 0 ? -100 : 0)));
            }
            if (this.calculate_discount == true){
                this.calculate_discount = false;
                this.currentOrder.total_with_tax_discount = this.currentOrder.get_total_with_tax();
                this.currentOrder.discount_total = discount_total;
            }
        }
    }
})