import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(vals);
    },
    set_fiscal_invoice_number(value) {
        this.fiscal_invoice_number = value;
    },
    get_fiscal_invoice_number(){
        return this.fiscal_invoice_number;
    },
    set_printer_serial(value) {
        this.printer_serial = value;
    },
    get_printer_serial(){
        return this.printer_serial;
    }
});