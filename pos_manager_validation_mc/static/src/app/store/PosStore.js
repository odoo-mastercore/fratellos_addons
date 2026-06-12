import { _t } from "@web/core/l10n/translation";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ask, makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { useBarcodeReader } from "@point_of_sale/app/barcode/barcode_reader_hook";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
let check_order_delete = true;
let check_close_pos = true;

patch(PosStore.prototype, {
    add_new_order(data = {}) {
        var res = super.add_new_order(data = {});
        res.pos = this;
        return res;
    },
    async checkPswd(type, pos_category_id, product_id, pos_payment_method_id, pos_order_id, partner_id){
        let self = this;
        let res = false;
        const posEmployeeSupervisor = this.getEmployeeSupervisor();
        const employee = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Seleccione el supervisor"),
            list: posEmployeeSupervisor,
        });
        var empObj = (employee != null ? employee : 0);
        if (employee) {
            var inputPin = await makeAwaitable(this.dialog, TextInputPopup, {
                    title:  _t("¿Contraseña?"),
                    startingValue: '',
                    type_password: true,
            });
            while (inputPin == undefined) {
                 inputPin = await makeAwaitable(this.dialog, TextInputPopup, {
                    title:  _t("¿Contraseña?"),
                    startingValue: '',
                    type_password: true,
                });   
            }
            if (inputPin) {
                if (employee._pin == Sha1.hash(inputPin)){
                    res = true;
                    this.saveAccessHistory(type, empObj.id, res, pos_category_id, product_id, pos_payment_method_id, pos_order_id, partner_id);
                }else{
                    this.notification.add(_t("PIN no encontrado"), {
                        type: "warning",
                        title: _t(`PIN incorrecto`),
                    });
                    this.saveAccessHistory(type, empObj.id, res, pos_category_id, product_id, pos_payment_method_id, pos_order_id, partner_id);
                }
            }
        }
        return res;
    },
    async saveAccessHistory(type, employee_id, result, pos_category_id, product_id, pos_payment_method_id, pos_order_id, partner_id){
        let accessHistory = {
            'name': type,
            'session_id': this.config.session_ids[0].id,
            'employee_id': employee_id,
            'pos_category_id': pos_category_id,
            'product_id': product_id,
            'pos_payment_method_id': pos_payment_method_id,
            'pos_order_id': pos_order_id,
            'partner_id': partner_id,
            'state': (result == true ? 'successful' : 'fail'),
        }
        var pos_access;
        try{
            var pos_access  = await this.data.call(
                "pos.access.history",
                "create_from_ui",
                [accessHistory],
                {},
                true
            );
        } catch (error) {
            console.log('Error while making the RPC call:', error);
        }
        return pos_access;
    },
    getEmployeeSupervisor() {
        const employeeList = this.config.advanced_employee_ids.map((employee_id) => ({
            id: employee_id.id,
            label: employee_id.name,
            isSelected: false,
            item: employee_id,
        }));
        return employeeList;
    },
    async onDeleteOrder(order) { 
        let config = this.config;
        let config_otp = config.one_time_valid;
        let result = true;
        if(config.order_delete && check_order_delete){
            result = await this.checkPswd('order_delete', false, false, false, false, (order.get_partner() != undefined ? order.get_partner().id : false));
        }
        if(result){
           return await super.onDeleteOrder(order);
        }
    },
    async closeSession() {
        let config = this.config;
        let config_otp = config.one_time_valid;
        let result = true;
        if(config.close_pos && check_close_pos){
            result = await this.checkPswd('close_pos', false, false, false, false, false);
        }
        if(result){
           await super.closeSession();
        }
    }
});