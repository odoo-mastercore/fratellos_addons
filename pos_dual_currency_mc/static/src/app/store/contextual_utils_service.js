import { contextualUtilsService } from "@point_of_sale/app/utils/contextual_utils_service";
import { registry } from "@web/core/registry";
import { formatCurrency as webFormatCurrency } from "@web/core/currency";
import {
    formatFloat,
    roundDecimals,
    floatIsZero as genericFloatIsZero,
} from "@web/core/utils/numbers";
import { escapeRegExp } from "@web/core/utils/strings";
import { parseFloat } from "@web/views/fields/parsers";

const extendedService = {
    ...contextualUtilsService,
    async start(env, { pos, localization }) {
        await contextualUtilsService.start(env, { pos, localization });
        const { res_currency } = pos;
        const formatCurrencyForeign = (value, show_currency_id, hasSymbol = true) => {
            return webFormatCurrency(value, show_currency_id, {
                noSymbol: !hasSymbol,
            });
        };
        const parseValidFloat = (inputValue) => {
            if (inputValue.indexOf('.') >= 0 && inputValue.indexOf(',') == (-1)){
                inputValue = inputValue.replace('.',',');
                //console.log('parseValidFloat-inputValue(F): ', inputValue);
            }
            return env.utils.isValidFloat(inputValue) ? parseFloat(inputValue) : 0;
        }
        env.utils.formatCurrencyForeign = formatCurrencyForeign;
        env.utils.parseValidFloat = parseValidFloat;
        //console.log('contextualUtilsService-utils: ', env.utils);
    }
};

registry.category("services").remove("contextual_utils_service");
registry.category("services").add("contextual_utils_service", extendedService);