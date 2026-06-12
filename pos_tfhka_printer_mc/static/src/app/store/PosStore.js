import { _t } from "@web/core/l10n/translation";
import { sprintf } from "@web/core/utils/strings";
import { parseFloat } from "@web/views/fields/parsers";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { DatePickerPopup } from "@point_of_sale/app/utils/date_picker_popup/date_picker_popup";
import { ask, makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { enhancedButtons } from "@point_of_sale/app/generic_components/numpad/numpad";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { compute_price_force_price_include } from "@point_of_sale/app/models/utils/tax_utils";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";
import { roundCurrency, formatCurrency } from "@point_of_sale/app/models/utils/currency";
//import { usePopup } from "@odoo/owl";
//const { showPopup } = usePopup();

patch(PosStore.prototype, {
    async ensureCryptoJS() {
        if (typeof CryptoJS === 'undefined') {
            await new Promise((resolve, reject) => {
                const script = document.createElement("script");
                script.src = "/pos_tfhka_printer_mc/static/src/lib/crypto-js/crypto-js.min.js";
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        }
    },
    async send_print_request(self, data, buttonAction = '.print-receipt-fiscal'){
        try{
            const response = await fetch("http://localhost:4000/document", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
                cache: "no-store", // similar a cache: false en $.ajax
            });
            if (!response.ok) {
                // Error HTTP
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        
            const json = await response.json();
            
            if (json.message.code !== "00") {
                this.dialog.add(AlertDialog, {
                    title: _t(json.message.title),
                    body: _t(json.message.description),
                });
            }
            return json;
        }catch (error) {
            //$('div.buttons div.button.print').attr('style','opacity: 1.0; pointer-events: auto;');
            this.dialog.add(AlertDialog, {
                title: _t("Servicio no encontrado"),
                body: _t("Verifique el estado del aplicativo"),
            });
            document.querySelector(buttonAction).style.opacity = "1.0";
            document.querySelector(buttonAction).style.pointerEvents = "auto";
            console.error("Error en la solicitud fetch:", error);
        }
    },
    async send_print_action(self, model, action, data){
        try{
            var send_url = 'http://localhost:4000/getPrinterData';
            const response = await fetch(send_url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
                cache: "no-store", // similar a cache: false en $.ajax
            });
            if (!response.ok) {
                // Error HTTP
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const json = await response.json();
            if (json.message.code != undefined){
                setTimeout(() => {
                    self.send_print_action(self, model, action, data);
                }, 5000);
            }else{
                if (action == 1 || action == 2){
                    self.set_fiscal_invoice_number(self, model, action, json);
                }
            }
        }catch (error) {
            //$('div.buttons div.button.print').attr('style','opacity: 1.0; pointer-events: auto;');
            this.dialog.add(AlertDialog, {
                title: _t("Servicio no encontrado"),
                body: _t("Verifique el estado del aplicativo"),
            });
            document.querySelector(".print-receipt-fiscal").style.opacity = "1.0";
            document.querySelector(".print-receipt-fiscal").style.pointerEvents = "auto";
            console.error("Error en la solicitud fetch:", error);
        }
    },
    async set_fiscal_invoice_number(self, model, action, json){
        if (json.message.code == undefined){
            model._printed_ready = true;
            try{
                /*var data = await self.env.services.rpc({
                    model: 'pos.order',
                    method: 'set_fiscal_invoice_number',
                    args: [model.id, model.access_token, action, json.message]
                });*/
                var data = await self.data.call(
                    "pos.order",
                    "set_fiscal_invoice_number",
                    [model.id, model.access_token, action, json.message],
                    {},
                    true
                );
            } catch (error) {
                console.log('Error while making the RPC call:', error);
                for (var i = 0; i < self.pos.db.get_orders().length; i++){
                    if (self.pos.db.get_orders()[i].data.access_token == model.access_token){
                        //console.log('get_orders-value: ', self.pos.db.get_orders()[i]);
                        self.pos.db.get_orders()[i].data.printer_serial = json.message.registeredMachineNumber;
                        self.pos.db.get_orders()[i].data.fiscal_invoice_number = self.pos.db.get_orders()[i].data.amount_total_foreign > 0 ? json.message.lastInvoiceNumber : json.message.lastNCNumber;
                        //console.log('get_orders-value: ', self.pos.db.get_orders()[i]);
                        return false;
                    }
                }
            }
            console.log('data:', data);
            if (data != undefined){
                document.querySelector(".print-receipt-fiscal").style.opacity = "1.0";
                document.querySelector(".print-receipt-fiscal").style.pointerEvents = "auto";
                if (data.code == '00'){
                    model._printed_ready = true;
                    this.get_order().set_fiscal_invoice_number(this.get_order().get_total_with_tax() > 0 ? json.message.lastInvoiceNumber : json.message.lastNCNumber);
                    this.get_order().set_printer_serial(json.message.registeredMachineNumber);
                }else{
                    for (var i = 0; i < self.pos.db.get_orders().length; i++){
                        if (self.pos.db.get_orders()[i].data.access_token == model.access_token){
                            //console.log('get_orders-value: ', self.pos.db.get_orders()[i]);
                            self.pos.db.get_orders()[i].data.printer_serial = json.message.registeredMachineNumber;
                            self.pos.db.get_orders()[i].data.fiscal_invoice_number = self.pos.db.get_orders()[i].data.amount_total_foreign > 0 ? json.message.lastInvoiceNumber : json.message.lastNCNumber;
                            //console.log('get_orders-value: ', self.pos.db.get_orders()[i]);
                            return false;
                        }
                    }
                    self.dialog.add(AlertDialog, {
                        title: _t('Error de actualizacion'),
                        body: _t(data.description),
                    });
                }
            }
            return data;
        }
        if (json.message.code != undefined && json.message.code != '00'){
            self.dialog.add(AlertDialog, {
                title: _t(json.message.title),
                body: _t(json.message.description),
            });
            document.querySelector(".print-receipt-fiscal").style.opacity = "1.0";
            document.querySelector(".print-receipt-fiscal").style.pointerEvents = "auto";$
        }
    },
    formatString(data){
        if (typeof data !== "string") return "";
        // Reemplazos de tildes y letras especiales primero
        const normalized = data.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    
        // Reemplazos personalizados (letras no latinas comunes y símbolos problemáticos)
        const customReplacements = normalized
            .replace(/ñ/g, 'n').replace(/á/g, 'a').replace(/é/g, 'e').replace(/í/g, 'i').replace(/ó/g, 'o').replace(/ú/g, 'u')
            .replace(/Ñ/g, 'N').replace(/Á/g, 'A').replace(/É/g, 'E').replace(/Í/g, 'I').replace(/Ó/g, 'O').replace(/Ú/g, 'U')
            .replace(/×/g, 'x').replace(/à/g, 'a').replace(/è/g, 'e').replace(/ì/g, 'i').replace(/ò/g, 'o').replace(/ù/g, 'u')
            .replace(/┴/g, 'A').replace(/À/g, 'A').replace(/È/g, 'E').replace(/Ì/g, 'I').replace(/Ò/g, 'O').replace(/Ù/g, 'U');
    
        // Eliminamos cualquier carácter no permitido:
        // Permitimos: letras, números, espacios y signos de puntuación básicos como ()[]{}:;?¿! --> /[^a-zA-Z0-9 \(\)\[\]\{\}\:\;\?\¿\!\,\.]/g
        const cleaned = customReplacements.replace(/[^a-zA-Z0-9&,. ]/g, '');

        // Espacios extra
        return cleaned.trim();
    },
    async reprintReceiptFiscal({
        basic = false,
        order = this.get_order(),
        printBillActionTriggered = false,
    } = {}) {
        try {
            document.querySelector(".print-receipt-fiscal").style.opacity = "0.4";
            document.querySelector(".print-receipt-fiscal").style.pointerEvents = "none";
            var url = 'http://localhost:4000/getReadFiscalMemoryByNumber';
            var nro_doc = order.fiscal_invoice_number.toString() || '';
            while (nro_doc.length < 7){
                nro_doc = "0" + nro_doc;
            }
            //console.log('nro_doc: ', nro_doc);
            var command;
            if (order.get_total_with_tax() > 0){
                command = 'RF' + nro_doc + nro_doc;
            }else{
                command = 'RC' + nro_doc + nro_doc;
            }
            var data = [];
            var data_print = {};
            data.push(command);
            data_print['message'] = data;
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data_print),
                cache: "no-store", // similar a cache: false en $.ajax
            });
            if (!response.ok) {
                // Error HTTP
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        
            const json = await response.json();
        
            if (json.message.code !== "00") {
                this.dialog.add(AlertDialog, {
                    title: _t(json.message.title),
                    body: _t(json.message.description),
                });
            }
            document.querySelector(".print-receipt-fiscal").style.opacity = "1.0";
            document.querySelector(".print-receipt-fiscal").style.pointerEvents = "auto";
        }catch (error) {
            //$('div.buttons div.button.print').attr('style','opacity: 1.0; pointer-events: auto;');
            this.dialog.add(AlertDialog, {
                title: _t("Servicio no encontrado"),
                body: _t("Verifique el estado del aplicativo"),
            });
            document.querySelector(".print-receipt-fiscal").style.opacity = "1.0";
            document.querySelector(".print-receipt-fiscal").style.pointerEvents = "auto";
            console.error("Error en la solicitud fetch:", error);
        }
    },
    async printReceiptFiscal({
        basic = false,
        order = this.get_order(),
        printBillActionTriggered = false,
    } = {}) {
        try {
            console.log('printReceiptFiscal-this: ', this);
            console.log('printReceiptFiscal-order: ', order);
            console.log('printReceiptFiscal-get_total_without_tax: ', order.get_total_with_tax());
            console.log('printReceiptFiscal-demo_printer_tfhka: ', this.config.demo_printer_tfhka);
            //console.log('printReceiptFiscal-demo_printer_tfhka: ', demo_printer_tfhka);
            //$('div.receipt-options button.print-receipt-fiscal').attr('style','opacity: 0.5; pointer-events: none;');
            document.querySelector(".print-receipt-fiscal").style.opacity = "0.4";
            document.querySelector(".print-receipt-fiscal").style.pointerEvents = "none";
            if (this.config.demo_printer_tfhka == undefined || this.config.demo_printer_tfhka == false){
                let credit_note = false
                if (order.get_total_with_tax() < 0){
                    credit_note = true;
                }
                console.log('printReceiptFiscal-credit_note: ', credit_note);
                console.log('printReceiptFiscal-_printed_ready: ', order._printed_ready);
                if (!credit_note){
                    //console.log('ReceiptScreen-constructor-this.currentOrder: ', this.currentOrder);
                    if(!order._printed_ready){
                        //console.log('printReceiptFiscal-this: ', this);
                        //var order = this.currentOrder;
                        console.log('printReceiptFiscal-order: ', order);
                        ////console.log('printReceiptFiscal-order.payment_ids: ', order.payment_ids);
                        var data = []
                        var data_print = {}
                        var client = order.get_partner();
                        console.log('printReceiptFiscal-client: ', client);
                        var l10n_ve_code = '';
                        /*for (var i = 0; i < this.l10n_latam_identification_type.length; i++){
                            if (client.l10n_latam_identification_type_id[0] == this.l10n_latam_identification_type[i].id){
                               l10n_ve_code = this.l10n_latam_identification_type[i].l10n_ve_code;
                            }
                        }*/
                        var i,j = "";
                        data.push("iR*"+ (client != undefined && client.vat ? l10n_ve_code + client.vat.toUpperCase() : ' '));
                        data.push("iS*" + (client != undefined && client.name ? this.formatString(client.name) : ' '));
                        data.push("i00Direccion: " + (client != undefined && client.street ? this.formatString(client.street) : ' '));
                        data.push("i01Telefono: " + (client != undefined && client.phone ? this.formatString(client.phone) : ' '));
                        data.push("i02Cajero: " + (order.employee_id != undefined ? this.formatString(order.employee_id.name) : ''));
                        var order_name = order.name.split(' ');
                        console.log('printReceiptFiscal-order_name: ', order_name);
                        data.push("i03Pedido: " + (order_name.length > 1 ? this.formatString(order_name[order_name.length - 1].replace('/','')) : ''));
                        var lineDoc = 0;
                        if (this.config.add_additional_information_header == true){
                            var message = this.config.additional_information_header.toString().trim();
                            var mesArray = message.split('\n');
                            var lineAdd = 4;
                            for (var i = 0; i < mesArray.length; i++){
                                if (lineAdd < 10){
                                    if (mesArray[i].toString().length > 40){
                                        var msj = this.formatString(mesArray[i].toString());
                                        while (msj.length > 0){
                                            if (lineAdd < 10){
                                                data.push("i0" + lineAdd.toString() + msj.substr(0, (msj.length > 40 ? 40:msj.length)));
                                                if (msj.length > 40){
                                                    msj = msj.substr(40, msj.length);
                                                }else{
                                                    msj = '';
                                                }
                                                lineAdd = lineAdd + 1;
                                            }else{
                                                msj = '';
                                            }
                                        }
                                    }else{
                                        data.push("i0" + lineAdd.toString() + mesArray[i].toString());
                                        lineAdd = lineAdd + 1;
                                    }
                                }
                            }
                        }
                        var i = 0;
                        var apply_igtf = false;
                        console.log('printReceiptFiscal-data(header): ', data);
                        var calculate_product_price_tfhka = this.config.calculate_product_price_tfhka;
                        //console.log('printReceiptFiscal-calculate_product_price_tfhka: ', calculate_product_price_tfhka);
                        for (const item of order.payment_ids) {
                            if (item.payment_method_id.is_igtf == true){
                                apply_igtf = true;
                            }
                        }
                        console.log('printReceiptFiscal-apply_igtf: ', apply_igtf);
                        if (apply_igtf == true){
                            data.push("PJ5001");
                        }
                        var ignore_product = 0.0;
                        var tax_prev;
                        var price_prev;
                        for (const item of order.get_orderlines()) {
                            console.log('printReceiptFiscal-item: ', item);
                            if (item.product_id.ignore_send_fiscal_printer != true){
                                var order_i = item;
                                var price = order_i.price_unit_foreign;
                                var tax = order_i.product_id.taxes_id || [];
                                console.log('printReceiptFiscal-order_i: ', order_i);
                                //console.log('printReceiptFiscal-price: ', price);
                                if (price < 0){
                                    tax = tax_prev;
                                    if (tax.length > 0 && tax[0].amount > 0 && calculate_product_price_tfhka == 'default'){
                                       price = roundPrecision(price / (1 + (tax[0].amount / 100)), 0.010000).toFixed(parseInt(priceLen[2]));
                                    }
                                }
                                if (item.discount != undefined && item.discount != 0){
                                    price = item.getUnitDisplayPriceBeforeDiscount();
                                    price = price * order.currency_rate_foreign;
                                    /*if (this.config.iface_tax_included == 'total'){
                                        price = roundPrecision((price / (1 + ((tax.length > 0 ? 0.0 : tax[0].amount)/100))), 0.010000);
                                    }*/
                                    //console.log('printReceiptFiscal-price-discount: ', price);
                                }
                                var priceLen = this.config.printer_tfhka_flag_21.split('_');
                                if (calculate_product_price_tfhka == 'tax_base'){
                                    if (tax.length > 0 && tax[0].amount > 0){
                                       price = (price / (1 + (tax[0].amount / 100)));
                                    }
                                }
                                if (calculate_product_price_tfhka == 'add_tax'){
                                    if (tax.length > 0 && tax[0].amount > 0){
                                       price = (price * (1 + (tax[0].amount / 100)));
                                    }
                                }
                                /*console.log('printReceiptFiscal-priceLen: ', priceLen);
                                console.log('printReceiptFiscal-price: ', price);
                                console.log('printReceiptFiscal-priceLen(2): ', parseInt(priceLen[2]));*/
                                var roundPrecisionFormat = 0.010000;
                                if (parseInt(priceLen[2]) == 2){
                                    roundPrecisionFormat = 0.010000;
                                }else if (parseInt(priceLen[2]) == 3){
                                    roundPrecisionFormat = 0.001000;
                                }else if (parseInt(priceLen[2]) == 4){
                                    roundPrecisionFormat = 0.000100;
                                }else if (parseInt(priceLen[2]) == 1){
                                    roundPrecisionFormat = 0.100000;
                                }else if (parseInt(priceLen[2]) == 0){
                                    roundPrecisionFormat = 0.000000;
                                }
                                var price_str = roundPrecision(price, roundPrecisionFormat).toFixed(parseInt(priceLen[2])).toString();
                                //console.log('printReceiptFiscal-price_str: ', price_str);
                                var quantity = order_i.qty;
                                var quantity_str = roundPrecision(quantity, 0.001000).toFixed(3).toString();
                                //console.log('printReceiptFiscal-quantity_str: ', quantity_str);
                                var tax_str = " "
                                price = roundPrecision(price, roundPrecisionFormat).toFixed(parseInt(priceLen[2]));
                                i = i + 1;
                                /*console.log('printReceiptFiscal-tax: ', tax);
                                console.log('printReceiptFiscal-length: ', tax.length);
                                console.log('printReceiptFiscal-tax_amount: ', order_i.product_id.tax_amount);*/
                                if (tax.length > 0){
                                    if (tax[0].amount == 16){
                                        tax_str = '!';
                                    }else if (tax[0].amount == 8){
                                        tax_str = '"';
                                    }else if (tax[0].amount == 31){
                                        tax_str = '#';
                                    }
                                }
                                //console.log('printReceiptFiscal-price(F): ', price);
                                if (Number.isNaN(price)){
                                    price = order_i.price_unit_foreign;
                                    if (calculate_product_price_tfhka == 'tax_base'){
                                        if (tax.length > 0 && order_i.product_id.tax_amount > 0){
                                           price = roundPrecision(price / (1 + (tax[0].amount / 100)), 0.010000).toFixed(parseInt(priceLen[2]));
                                        }
                                    }
                                    if (calculate_product_price_tfhka == 'add_tax'){
                                        if (tax.length > 0 && order_i.product_id.tax_amount > 0){
                                           price = roundPrecision((price * (1 + (tax[0].amount / 100))), 0.010000).toFixed(parseInt(priceLen[2]));
                                        }
                                    }
                                    //console.log('printReceiptFiscal-price(NaN)(F): ', price);
                                }
                                if (price > 0){
                                    if(parseInt(priceLen[0]) == 30){
                                        quantity_str = quantity_str.padStart(18, 0).replaceAll('.', '')
                                    }else{
                                        quantity_str = quantity_str.padStart(9, 0).replaceAll('.', '')
                                    }
                                    //console.log('printReceiptFiscal-quantity_str(padStart): ', quantity_str);
                                    data.push(tax_str + price_str.replaceAll('.', '').padStart((parseInt(priceLen[1]) + parseInt(priceLen[2])), 0) + quantity_str + this.formatString(order_i.product_id.display_name));
                                    if (item.discount != undefined && item.discount > 0){
                                        var pdiscount = roundPrecision(item.discount, 0.010000).toFixed(2);
                                        data.push("p-" + pdiscount.toString().replaceAll('-', '').replaceAll('.', '').padStart(2, 0));
                                    }
                                    tax_prev = tax;
                                    price_prev = price * quantity;
                                }else{
                                    if (priceLen[0].toString() == "00" || priceLen[0].toString() == "02" || priceLen[0].toString() == "11" || priceLen[0].toString() == "12"){
                                        priceLen[1] = (parseInt(priceLen[1]) - 1).toString();
                                    }else if(priceLen[0].toString() == "30"){
                                        priceLen[1] = (parseInt(priceLen[1]) + 1).toString();
                                    }
                                    //console.log('printReceiptFiscal-price(r): ', price);
                                    //console.log('printReceiptFiscal-price_prev(r): ', price_prev);
                                    if ((price * -1) > price_prev){
                                        data.push("3");
                                    }
                                    data.push("q-" + price_str.replaceAll('-', '').replaceAll('.', '').padStart((parseInt(priceLen[1]) + parseInt(priceLen[2])), 0));
                                    data.push('@DESCUENTO DE MONTO FIJO')
                                    tax_prev = tax;
                                    price_prev = price * quantity;
                                }
                            }else{
                                //console.log('printReceiptFiscal-product: ', item.product);
                                //console.log('printReceiptFiscal-lst_price: ', item.product_id.lst_price);
                                ignore_product = ignore_product + roundPrecision((item.price_unit_foreign * item.quantity), 0.010000);
                            }
                        }
                        //console.log('printReceiptFiscal-ignore_product: ', ignore_product);
                        data.push("3");
                        for (const item of order.payment_ids) {
                            //console.log('printReceiptFiscal-get_paymentlines(item): ', item);
                            //console.log('printReceiptFiscal-amount: ', item.amount);
                            //console.log('printReceiptFiscal-amount_foreign: ', item.amount_foreign);
                            let pay_price = 0.0;
                            if (item.payment_method_id.enable_currencies == false){
                                pay_price = (item.igtf_base == undefined ? (item.amount * order.currency_rate_foreign) : item.igtf_base);
                            }else{
                                pay_price = (item.igtf_base == undefined ? item.amount_foreign : item.igtf_base);
                            }
                            if (ignore_product > 0.0){
                                //console.log('printReceiptFiscal-pay_price: ', pay_price);
                                if (pay_price > ignore_product){
                                    pay_price = pay_price - ignore_product;
                                    ignore_product = 0.0;
                                }
                                //console.log('printReceiptFiscal-pay_price(F): ', pay_price);
                            }
                            let str_pay_price = '';
                            pay_price = roundPrecision(pay_price, 0.001000);
                            //console.log('printReceiptFiscal-pay_price: ', pay_price);
                            if(parseInt(priceLen[0]) == 30){
                                str_pay_price = pay_price.toFixed(2).toString().replaceAll(".","").padStart(17,"0");
                            }else{
                                str_pay_price = pay_price.toFixed(2).toString().replaceAll(".","").padStart(12,"0");
                            }
                            //console.log('printReceiptFiscal-str_pay_price: ', str_pay_price);
                            data.push('2'+ (item.payment_method_id.code_in_printer_tfhka != false ? item.payment_method_id.code_in_printer_tfhka : '01') + str_pay_price)
                        }
                        if (this.config.version_tfhka == 'V8_5_0'){
                            data.push("101")
                            data.push("199")
                        }else if (this.config.version_tfhka == 'V1_SRP_812'){
                            data.push("101");
                            if (apply_igtf == true){
                                data.push("199");
                            }
                        }else{
                            data.push("101")
                            data.push("119");
                            if (apply_igtf == true){
                                data.push("199");
                            }
                        }
                        if (this.config.add_additional_information_footer == true){
                            var message = this.config.additional_information_footer.toString().trim();
                            var mesArray = message.split('\n');
                            var lineAdd = 1;
                            for (var i = 0; i < mesArray.length; i++){
                                if (lineAdd < 10){
                                    if (mesArray[i].toString().length > 40){
                                        var msj = this.formatString(mesArray[i].toString());
                                        while (msj.length > 0){
                                            if (lineAdd < 10){
                                                data.push("i0" + lineAdd.toString() + msj.substr(0, (msj.length > 40 ? 40:msj.length)));
                                                if (msj.length > 40){
                                                    msj = msj.substr(40, msj.length);
                                                }else{
                                                    msj = '';
                                                }
                                                lineAdd = lineAdd + 1;
                                            }else{
                                                msj = '';
                                            }
                                        }
                                    }else{
                                        data.push("i0" + lineAdd.toString() + mesArray[i].toString());
                                        lineAdd = lineAdd + 1;
                                    }
                                }
                            }
                        }
                        lineDoc = data.length;
                        console.log('printReceiptFiscal-data: ', data);
                        data_print['message'] = data
                        data_print['uid'] = order.access_token;
                        await this.ensureCryptoJS();
                        console.log('printReceiptFiscal-this: ', this);
                        console.log('printReceiptFiscal-url_access: ', this.config.url_access);
                        console.log('printReceiptFiscal-key: ', this.config.url_access + order.access_token);
                        data_print['access'] = CryptoJS.SHA256(this.config.url_access + order.access_token).toString();
                        console.log('printReceiptFiscal-data: ', data_print);
                        var res = await this.send_print_request(this, data_print);
                        console.log('printReceiptFiscal-res: ', res);
                        if (res != undefined){
                            // Generacion S1
                            var dataStatus = []
                            var data_status_print = {}
                            var res_status;
                            //setTimeout(() => {
                            dataStatus.push("S1");
                            data_status_print['message'] = dataStatus
                            this.send_print_action(this, order, 1, data_status_print);
                                //this.props.order._printed_ready = true;
                            //}, (lineDoc * (this.config.time_printer_tfhka_doc > 0 ? this.config.time_printer_tfhka_doc : 500)));
                            order._printed_ready = true;   
                        }
                    }else{
                        this.dialog.add(AlertDialog, {
                            title: _t('Error al imprimir'),
                            body: _t('Esta factura ya ha sido impresa.'),
                        });
                        document.querySelector(".print-receipt-fiscal").style.opacity = "1.0";
                        document.querySelector(".print-receipt-fiscal").style.pointerEvents = "auto";
                    }
                } else {
                    if(!order._printed_ready){
                        var buttons = [];
                        var number_invoice = await makeAwaitable(this.dialog, TextInputPopup, {
                            title:  _t("Ingrese el número de factura afectada"),
                            buttons,
                            rows: 1,
                            startingValue: order.refunded_order_id.fiscal_invoice_number.toString() || '',
                        });
                        console.log('number_invoice: ', number_invoice);
                        if (number_invoice == undefined){
                            this.dialog.add(AlertDialog, {
                                title: _t("Dato inválido"),
                                body: _t("Es obligatorio ingresar el número de factura"),
                            });
                            document.querySelector(".print-receipt-fiscal").style.opacity = "1.0";
                            document.querySelector(".print-receipt-fiscal").style.pointerEvents = "auto";
                            return;
                        }
                        var date_invoice = await makeAwaitable(this.dialog, DatePickerPopup, {
                            title: _t("Ingrese la fecha de la factura afectada"),
                            min_date: order.refunded_order_id.date_order.substr(0, 10),
                        });
                        console.log('date_invoice: ', date_invoice);
                        if (date_invoice == undefined){
                            this.dialog.add(AlertDialog, {
                                title: _t("Dato inválido"),
                                body: _t("Es obligatorio ingresar la fecha de la Factura"),
                            });
                            document.querySelector(".print-receipt-fiscal").style.opacity = "1.0";
                            document.querySelector(".print-receipt-fiscal").style.pointerEvents = "auto";
                            return;
                        }
                        var control_invoice = await makeAwaitable(this.dialog, TextInputPopup, {
                            title:  _t("Ingrese el serial de la impresora fiscal asociada a la factura"),
                            buttons,
                            rows: 1,
                            startingValue: order.refunded_order_id.printer_serial || '',
                        });
                        control_invoice = control_invoice.toUpperCase();
                        console.log('control_invoice: ', control_invoice);
                        if (control_invoice == undefined){
                            this.dialog.add(AlertDialog, {
                                title: _t("Dato inválido"),
                                body: _t("Es obligatorio ingresar el serial de la impresora fiscal"),
                            });
                            document.querySelector(".print-receipt-fiscal").style.opacity = "1.0";
                            document.querySelector(".print-receipt-fiscal").style.pointerEvents = "auto";
                            return;
                        }
                        // Devolucion
                        //var order = this.currentOrder;
                        var data = []
                        var data_print = {}
                        var client = order.get_partner();
                        var l10n_ve_code = '';
                        /*for (var i = 0; i < this.l10n_latam_identification_type.length; i++){
                            if (client.l10n_latam_identification_type_id[0] == this.l10n_latam_identification_type[i].id){
                               l10n_ve_code = this.l10n_latam_identification_type[i].l10n_ve_code;
                            }
                        }*/
                        data.push("iF*"+ number_invoice);
                        data.push("iD*"+ date_invoice);
                        data.push("iI*"+ control_invoice);
                        data.push("iR*"+ (client != undefined && client.vat ? l10n_ve_code + client.vat.toUpperCase() : ' '));
                        data.push("iS*" + (client != undefined && client.name ? this.formatString(client.name) : ' '));
                        var order_name = order.name.split(' ');
                        data.push("i02Cajero: " + (order.employee_id != undefined ? this.formatString(order.employee_id.name) : ''));
                        data.push("i03Pedido: " + (order_name.length > 1 ? this.formatString(order_name[order_name.length - 1].replace('/','')) : ''));
                        var lineDoc = 0;
                        if (this.config.add_additional_information_header == true){
                            var message = this.config.additional_information_header.toString().trim();
                            var mesArray = message.split('\n');
                            var lineAdd = 2;
                            for (var i = 0; i < mesArray.length; i++){
                                if (lineAdd < 10){
                                    if (mesArray[i].toString().length > 40){
                                        var msj = this.formatString(mesArray[i].toString());
                                        while (msj.length > 0){
                                            if (lineAdd < 10){
                                                data.push("i0" + lineAdd.toString() + msj.substr(0, (msj.length > 40 ? 40:msj.length)));
                                                if (msj.length > 40){
                                                    msj = msj.substr(40, msj.length);
                                                }else{
                                                    msj = '';
                                                }
                                                lineAdd = lineAdd + 1;
                                            }else{
                                                msj = '';
                                            }
                                        }
                                    }else{
                                        data.push("i0" + lineAdd.toString() + mesArray[i].toString());
                                        lineAdd = lineAdd + 1;
                                    }
                                }
                            }
                        }
                        var apply_igtf = false;
                        var calculate_product_price_tfhka = this.config.calculate_product_price_tfhka;
                        //console.log('printReceiptFiscal-calculate_product_price_tfhka: ', calculate_product_price_tfhka);
                        for (const item of order.payment_ids) {
                            if (item.payment_method_id.is_igtf == true){
                                apply_igtf = true;
                            }
                        }
                        //console.log('printReceiptFiscal-apply_igtf: ', apply_igtf);
                        if (apply_igtf == true){
                            data.push("PJ5001");
                        }
                        var ignore_product = 0.0;
                        var tax_prev;
                        var price_prev;
                        for (const item of order.get_orderlines()) {
                            if (item.product_id.ignore_send_fiscal_printer != true){
                                var order_i = item
                                var price = order_i.price_unit_foreign;
                                var tax = order_i.product_id.taxes_id || [];
                                //console.log('printReceiptFiscal-price: ', price);
                                if (price < 0){
                                    tax = tax_prev;
                                    if (tax.length > 0 && tax[0].amount > 0 && calculate_product_price_tfhka == 'default'){
                                       price = roundPrecision(price / (1 + (tax[0].amount / 100)), 0.010000).toFixed(parseInt(priceLen[2]));
                                    }
                                }
                                if (item.discount != undefined && item.discount != 0){
                                    price = item.getUnitDisplayPriceBeforeDiscount();
                                    price = price * order.currency_rate_foreign;
                                    /*if (this.config.iface_tax_included == 'total'){
                                        price = roundPrecision((price / (1 + ((item.product_id.tax_amount == undefined ? 0.0:item.product_id.tax_amount)/100))), 0.010000);
                                    }*/
                                    //console.log('printReceiptFiscal-price-discount: ', price);
                                }
                                var priceLen = this.config.printer_tfhka_flag_21.split('_');
                                if (calculate_product_price_tfhka == 'tax_base'){
                                    if (tax.length > 0 && tax[0].amount > 0){
                                       price = (price / (1 + (tax[0].amount / 100)));
                                    }
                                }
                                if (calculate_product_price_tfhka == 'add_tax'){
                                    if (tax.length > 0 && tax[0].amount > 0){
                                       price = (price * (1 + (tax[0].amount / 100)));
                                    }
                                }
                                var roundPrecisionFormat = 0.010000;
                                if (parseInt(priceLen[2]) == 2){
                                    roundPrecisionFormat = 0.010000;
                                }else if (parseInt(priceLen[2]) == 3){
                                    roundPrecisionFormat = 0.001000;
                                }else if (parseInt(priceLen[2]) == 4){
                                    roundPrecisionFormat = 0.000100;
                                }else if (parseInt(priceLen[2]) == 1){
                                    roundPrecisionFormat = 0.100000;
                                }else if (parseInt(priceLen[2]) == 0){
                                    roundPrecisionFormat = 0.000000;
                                }
                                var price_str = roundPrecision(price, roundPrecisionFormat).toFixed(parseInt(priceLen[2])).toString();
                                //console.log('printReceiptFiscal-price_str: ', price_str);
                                var quantity = -1 * order_i.qty;
                                var quantity_str = roundPrecision(quantity, 0.001000).toFixed(3).toString();
                                var tax_str = "d0";
                                if (tax.length > 0){
                                    if (tax[0].amount == 16){
                                        tax_str = 'd1';
                                    }else if (tax[0].amount == 8){
                                        tax_str = 'd2';
                                    }else if (tax[0].amount == 31){
                                        tax_str = 'd3';
                                    }
                                }
                                //console.log('NC-price: ', price);
                                if (price > 0){
                                    if(parseInt(priceLen[0]) == 30){
                                        quantity_str = quantity_str.padStart(18, 0).replaceAll('.', '')
                                    }else{
                                        quantity_str = quantity_str.padStart(9, 0).replaceAll('.', '')
                                    }
                                    //console.log('printReceiptFiscal-quantity_str(padStart): ', quantity_str);
                                    data.push(tax_str + price_str.replaceAll('.', '').padStart((parseInt(priceLen[1]) + parseInt(priceLen[2])), 0) + quantity_str + this.formatString(order_i.product_id.display_name));
                                    if (item.discount != undefined && item.discount > 0){
                                        var pdiscount = roundPrecision(item.discount, 0.010000).toFixed(2);
                                        data.push("p+" + pdiscount.toString().replaceAll('-', '').replaceAll('.', '').padStart(2, 0));
                                    }
                                    tax_prev = tax;
                                    price_prev = price * quantity;
                                }else{
                                    if (priceLen[0].toString() == "00" || priceLen[0].toString() == "02" || priceLen[0].toString() == "11" || priceLen[0].toString() == "12"){
                                        priceLen[1] = (parseInt(priceLen[1]) - 1).toString();
                                    }else if(priceLen[0].toString() == "30"){
                                        priceLen[1] = (parseInt(priceLen[1]) + 1).toString();
                                    }
                                    //console.log('printReceiptFiscal-price(r): ', price);
                                    //console.log('printReceiptFiscal-price_prev(r): ', price_prev);
                                    if ((price * -1) > price_prev){
                                        data.push("3");
                                    }
                                    data.push("q-" + price_str.replaceAll('-', '').replaceAll('.', '').padStart((parseInt(priceLen[1]) + parseInt(priceLen[2])), 0));
                                    data.push('@DESCUENTO DE MONTO FIJO')
                                    tax_prev = tax;
                                    price_prev = price * quantity;
                                }
                            }else{
                                //console.log('printReceiptFiscal-product: ', item.product);
                                //console.log('printReceiptFiscal-lst_price: ', item.product_id.lst_price);
                                ignore_product = ignore_product + roundPrecision((item.price_unit_foreign * item.quantity), 0.010000);
                            }
                        }
                        data.push("3")
                        for (const item of order.payment_ids) {
                            //console.log('printReceiptFiscal-get_paymentlines(item): ', item);
                            //console.log('printReceiptFiscal-amount: ', item.amount);
                            //console.log('printReceiptFiscal-amount_foreign: ', item.amount_foreign);
                            let pay_price = 0.0;
                            if (item.payment_method_id.enable_currencies == false){
                                pay_price = -1 * (item.igtf_base == undefined ? (item.amount * order.currency_rate_foreign) : item.igtf_base);
                            }else{
                                pay_price = -1 * (item.igtf_base == undefined ? item.amount_foreign : item.igtf_base);
                            }
                            if (ignore_product > 0.0){
                                //console.log('printReceiptFiscal-pay_price: ', pay_price);
                                if (pay_price > ignore_product){
                                    pay_price = pay_price - ignore_product;
                                    ignore_product = 0.0;
                                }
                                //console.log('printReceiptFiscal-pay_price(F): ', pay_price);
                            }
                            pay_price = roundPrecision(pay_price, 0.001000);
                            let str_pay_price = '';
                            if(parseInt(priceLen[0] == 30)){
                                str_pay_price = pay_price.toFixed(2).toString().replaceAll(".","").padStart(17,"0");
                            }else{
                                str_pay_price = pay_price.toFixed(2).toString().replaceAll(".","").padStart(12,"0");
                            }
                            data.push('2'+ (item.payment_method_id.code_in_printer_tfhka != false ? item.payment_method_id.code_in_printer_tfhka : '01') + str_pay_price)
                        }
                        if (this.config.version_tfhka == 'V8_5_0'){
                            data.push("101")
                            data.push("199")
                        }else if (this.config.version_tfhka == 'V1_SRP_812'){
                            data.push("101")
                            if (apply_igtf == true){
                                data.push("199");
                            }
                        }else{
                            data.push("101")
                            data.push("119")
                            if (apply_igtf == true){
                                data.push("199");
                            }
                        }
                        if (this.config.add_additional_information_footer == true){
                            var message = this.config.additional_information_footer.toString().trim();
                            var mesArray = message.split('\n');
                            var lineAdd = 1;
                            for (var i = 0; i < mesArray.length; i++){
                                if (lineAdd < 10){
                                    if (mesArray[i].toString().length > 40){
                                        var msj = this.formatString(mesArray[i].toString());
                                        while (msj.length > 0){
                                            if (lineAdd < 10){
                                                data.push("i0" + lineAdd.toString() + msj.substr(0, (msj.length > 40 ? 40:msj.length)));
                                                if (msj.length > 40){
                                                    msj = msj.substr(40, msj.length);
                                                }else{
                                                    msj = '';
                                                }
                                                lineAdd = lineAdd + 1;
                                            }else{
                                                msj = '';
                                            }
                                        }
                                    }else{
                                        data.push("i0" + lineAdd.toString() + mesArray[i].toString());
                                        lineAdd = lineAdd + 1;
                                    }
                                }
                            }
                        }
                        lineDoc = data.length;
                        console.log('printReceiptFiscal-data: ', data);
                        data_print['message'] = data;
                        data_print['uid'] = order.access_token;
                        await this.ensureCryptoJS();
                        data_print['access'] = CryptoJS.SHA256(this.config.url_access + order.access_token).toString();
                        console.log('printReceiptFiscal-data: ', data_print);
                        var res = await this.send_print_request(this, data_print);
                        // Generacion S1
                        if (res != undefined){
                            var dataStatus = []
                            var data_status_print = {}
                            var res_status;
                            //setTimeout(() => {
                            dataStatus.push("S1");
                            data_status_print['message'] = dataStatus
                            this.send_print_action(this, order, 2, data_status_print);
                                //this.props.order._printed_ready = true;
                            //}, (lineDoc * (this.config.time_printer_tfhka_doc > 0 ? this.config.time_printer_tfhka_doc : 500)));
                            order._printed_ready = true;   
                        }
                        //this.props.order._printed_ready = true;
                    }else{
                        this.dialog.add(AlertDialog, {
                            title: _t('Error al imprimir'),
                            body: _t('Esta factura ya ha sido impresa.'),
                        });
                    }
                }
            }else{
                console.log('Entrando a impresión DEMO');
                $('div.buttons div.button.print').attr('style','opacity: 0.5; pointer-events: none;');
                //alert('documento de prueba')
                // Impresion de documento demo
                var data_demo = []
                var data_print_demo = {}
    
                data_demo.push('800Documento de prueba de impresion1')
                data_demo.push('80* test')
                data_demo.push('810Fin del Documento de prueba')
                // data_demo.push('I0X')
                data_print_demo['message'] = data_demo
                await this.send_print_request(this, data_print_demo);
                $('div.buttons div.button.print').attr('style','opacity: 1.0; pointer-events: auto;');
            }
        } catch (error) {
            console.error('Error:', error);
            return;
        }
    },
    async generateReportFiscal({
        basic = false,
        config = this.config,
        printBillActionTriggered = false,
    } = {}) {
        try {
            document.querySelector(".generate-report-fiscal-" + config.typeReport).style.opacity = "0.4";
            document.querySelector(".generate-report-fiscal-" + config.typeReport).style.pointerEvents = "none";
            var data = []
            var data_print = {}
            data.push('I0' + config.typeReport)
            data_print['message'] = data;
            data_print['uid'] = config.typeReport == 'X' ? 'a263cc7d9c21d9d57b3ffa98bf8d9168556f2d4bc3fde34be41641db5dc91f80' : '223c906fbaed009fcc9b9631903fb5293975106e1bbfd149197aeeea76e4e8d9';
            await this.ensureCryptoJS();
            data_print['access'] = CryptoJS.SHA256(this.config.url_access + data_print['uid']).toString();
            var res = await this.send_print_request(this, data_print, ('.generate-report-fiscal-' + config.typeReport));
            console.log('generateReportFiscal-res: ', res);
            if (res != undefined && res.message.code == '00' && config.typeReport == 'Z'){
                // Generacion S1
                var dataStatus = []
                var data_status_print = {}
                var res_status;
                //setTimeout(() => {
                dataStatus.push("S1");
                data_status_print['message'] = dataStatus
                var res_report = await this.send_print_action_report(this, data_status_print, ('.generate-report-fiscal-' + config.typeReport));
                console.log('generateReportFiscal-res_report: ', res_report);
                //}, (this.config.time_printer_tfhka_rep_z > 0 ? this.config.time_printer_tfhka_rep_z : 10000));   
            }
            document.querySelector(".generate-report-fiscal-" + config.typeReport).style.opacity = "1.0";
            document.querySelector(".generate-report-fiscal-" + config.typeReport).style.pointerEvents = "auto";
        }catch (error) {
            //$('div.buttons div.button.print').attr('style','opacity: 1.0; pointer-events: auto;');
            this.dialog.add(AlertDialog, {
                title: _t("Servicio no encontrado"),
                body: _t("Verifique el estado del aplicativo"),
            });
            document.querySelector(".generate-report-fiscal-" + config.typeReport).style.opacity = "1.0";
            document.querySelector(".generate-report-fiscal-" + config.typeReport).style.pointerEvents = "auto";
            console.error("Error en la solicitud fetch:", error);
        }
    },
    async send_print_action_report(self, data, buttonAction){
        try{
            var send_url = 'http://localhost:4000/getPrinterData';
            const response = await fetch(send_url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
                cache: "no-store", // similar a cache: false en $.ajax
            });
            if (!response.ok) {
                // Error HTTP
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const json = await response.json();
            if (json.message.code == undefined){
                var dataReport = {
                  "message": [
                    "I0Z",
                    "number",
                    json.message.dailyClosureCounter,
                    json.message.dailyClosureCounter
                  ]
                }
                const responseReport = await fetch('http://localhost:4000/getReport', {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(dataReport),
                    cache: "no-store", // similar a cache: false en $.ajax
                });
                if (!responseReport.ok) {
                    // Error HTTP
                    throw new Error(`HTTP error! status: ${responseReport.status}`);
                }
                const jsonReport = await responseReport.json();
                //console.log('mapped_create-self: ', self);
                jsonReport.registeredMachineNumber = json.message.registeredMachineNumber;
                jsonReport.config_id = self.config.id;
                jsonReport.company_id = self.company.id;
                jsonReport.pos_session_id = self.config.session_ids[0].id;
                console.log('mapped_create-jsonReport: ', jsonReport);
                var data = await self.data.call(
                    "fiscal.report.z",
                    "mapped_create",
                    [false, jsonReport],
                    {},
                    true
                );
                console.log('mapped_create-data: ', data);
                return data;
            }
            if (json.message.code != undefined && json.message.code != '00'){
                this.dialog.add(AlertDialog, {
                    title: _t(json.message.title),
                    body: _t(json.message.description),
                });
                document.querySelector(buttonAction).style.opacity = "1.0";
                document.querySelector(buttonAction).style.pointerEvents = "auto";
                return false;
            }
        }catch (error) {
            //$('div.buttons div.button.print').attr('style','opacity: 1.0; pointer-events: auto;');
            this.dialog.add(AlertDialog, {
                title: _t("Servicio no encontrado"),
                body: _t("Verifique el estado del aplicativo"),
            });
            document.querySelector(buttonAction).style.opacity = "1.0";
            document.querySelector(buttonAction).style.pointerEvents = "auto";
            return false;
        }
    }
});