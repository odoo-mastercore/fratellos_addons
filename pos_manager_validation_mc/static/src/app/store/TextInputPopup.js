import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(TextInputPopup.prototype, {

});
TextInputPopup.props.type_password = { type: Boolean, optional: true };