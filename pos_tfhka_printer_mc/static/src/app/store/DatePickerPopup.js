import { DatePickerPopup } from "@point_of_sale/app/utils/date_picker_popup/date_picker_popup";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(DatePickerPopup.prototype, {
    _today() {
        if (this.props.min_date != undefined){
            return this.props.min_date;   
        }else{
            return super._today();
        }
    }
});
DatePickerPopup.props.min_date = { type: String, optional: true };