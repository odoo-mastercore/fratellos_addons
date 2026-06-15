import { OpeningControlPopup } from "@point_of_sale/app/store/opening_control_popup/opening_control_popup";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { MoneyDetailsPopup } from "@point_of_sale/app/utils/money_details_popup/money_details_popup";
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Input } from "@point_of_sale/app/generic_components/inputs/input/input";
import { parseFloat } from "@web/views/fields/parsers";
import { Dialog } from "@web/core/dialog/dialog";
import { RPCError } from "@web/core/network/rpc";

patch(OpeningControlPopup.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        //console.log('OpeningControlPopup-session: ', this.pos.session);
        const payment_method_cash_ids = [];
        const bank_statement_balance_start = [];
        try {
            for (var i=0; i < this.pos.config.payment_method_ids.length; i++){
                if (this.pos.config.payment_method_ids[i].type == 'cash'){
                    var openingCash = 0.0;
                    for (var x = 0; x < this.pos.session.statement_ids.length; x++){
                        if (this.pos.config.opening_cash_mode == 'last_opening'){
                            openingCash = this.pos.session.statement_ids[x].balance_end;   
                        }else if (this.pos.config.opening_cash_mode == 'setting_amount' && this.pos.config.payment_method_ids[i].enable_amount_opening == true){
                            openingCash = this.pos.config.payment_method_ids[i].amount_opening || 0;
                        }else{
                            openingCash = 0.0;
                        }
                    }
                    //console.log('OpeningControlPopup-payment_method_ids: ', this.pos.config.payment_method_ids[i]);
                    //console.log('OpeningControlPopup-enable_currencies: ', this.pos.config.payment_method_ids[i].enable_currencies);
                    if (this.pos.config.payment_method_ids[i].enable_currencies == true){
                        payment_method_cash_ids.push({
                            'id': this.pos.config.payment_method_ids[i].id,
                            'journal_id': this.pos.config.payment_method_ids[i].journal_idx ,
                            'default': false,
                            'currency_rate': this.pos.config.payment_method_ids[i].currency_rate,
                            'name': this.pos.config.payment_method_ids[i].name,
                            'type': this.pos.config.payment_method_ids[i].type,
                            'isCashCount': this.pos.config.payment_method_ids[i].is_cash_count,
                            'splitTransactions': this.pos.config.payment_method_ids[i].split_transactions,
                            'usePaymentTerminal': this.pos.config.payment_method_ids[i].use_payment_terminal,
                            'enableCurrencies': this.pos.config.payment_method_ids[i].enable_currencies,
                            'enable_amount_opening': (this.pos.config.payment_method_ids[i].enable_amount_opening == true && this.pos.config.opening_cash_mode == 'setting_amount' ? true : false),
                            'openingCash': this.env.utils.formatCurrency(openingCash ,false), //bank_statement_balance_start[this.pos.config.payment_method_ids[i].id] || 0,
                        });
                    }else{
                        payment_method_cash_ids.push({
                            'id': this.pos.config.payment_method_ids[i].id,
                            'journal_id': this.pos.config.payment_method_ids[i].journal_idx,
                            'default': true,
                            'currency_rate': this.pos.config.payment_method_ids[i].currency_rate,
                            'name': this.pos.config.payment_method_ids[i].name,
                            'type': this.pos.config.payment_method_ids[i].type,
                            'isCashCount': this.pos.config.payment_method_ids[i].is_cash_count,
                            'splitTransactions': this.pos.config.payment_method_ids[i].split_transactions,
                            'usePaymentTerminal': this.pos.config.payment_method_ids[i].use_payment_terminal,
                            'enableCurrencies': this.pos.config.payment_method_ids[i].enable_currencies,
                            'enable_amount_opening': (this.pos.config.payment_method_ids[i].enable_amount_opening == true && this.pos.config.opening_cash_mode == 'setting_amount' ? true : false),
                            'openingCash': this.env.utils.formatCurrency(openingCash ,false), //bank_statement_balance_start[this.pos.config.payment_method_ids[i].id] || 0,
                        });
                    }
                }
            }   
        } catch (error) {
            console.log('error: ', error);
        }
        this.paymentMethodCash = payment_method_cash_ids;
        //console.log('OpeningControlPopup(F): ', this);
    },
    async confirm(){ //startSession() {
        const openingCash = {};
        for (var i=0; i < this.paymentMethodCash.length; i++){
            var regex = new RegExp(/^\+?[0-9(),.-]+$/);
            if (this.paymentMethodCash[i].openingCash == '' || this.paymentMethodCash[i].openingCash.match(regex) == null){
                this.dialog.add(AlertDialog, {
                    title: _t("Monto de apertura inválido"),
                    body: _t("Por favor ingrese un monto permitido."),
                });
                return false;
            }
            if (this.paymentMethodCash[i].default == true){
                openingCash[this.paymentMethodCash[i].id] = this.paymentMethodCash[i].openingCash;
            }else{
                openingCash[this.paymentMethodCash[i].id] = this.paymentMethodCash[i].openingCash;
            }
        }
        //console.log('confirm(this): ', this);
        //console.log('confirm(openingCash): ', openingCash);
        try {
            await this.pos.data.call(
                "pos.session",
                "set_opening_control_payment_method",
                [this.pos.session.id, this.paymentMethodCash, openingCash, this.state.notes],
                {},
                true
            );
        } catch (error) {
            if (
                error instanceof RPCError &&
                error.data.name === "odoo.exceptions.MissingError" &&
                (await this.pos.isSessionDeleted())
            ) {
                return window.location.reload();
            }
            throw error;
        }
        //super.confirm();
        this.pos.session.state = "opened";
        this.props.close();
    }
});