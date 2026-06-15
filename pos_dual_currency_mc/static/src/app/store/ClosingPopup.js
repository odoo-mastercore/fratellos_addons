import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";
import { ConnectionLostError } from "@web/core/network/rpc";
import { deduceUrl } from "@point_of_sale/utils";

const extendedProps = ClosePosPopup.props.concat([
    "rate",
    "payments_amount",
    "payments_amount_foreign",
    "pay_later_amount",
    "pay_later_amount_foreign",
    "currency_format",
]);

patch(ClosePosPopup, {
    props: extendedProps,
    
});

patch(ClosePosPopup.prototype, {
    setup() {
        super.setup();
        //console.log('ClosePosPopup-setup-this: ', this);
        //console.log("ClosePosPopup extendido - props:", this.props);
    },
    getInitialState(){
        var res = super.getInitialState();
        //console.log('ClosePosPopup-getInitialState-res: ', res);
        this.props.non_cash_payment_methods.forEach((pm) => {
            if (pm.type != "bank" && pm.type != "pay_later") {
                res.payments[pm.id] = {
                    counted: "0",
                };
            }
        });
        //console.log('ClosePosPopup-getInitialState-res(F): ', res);
        return res;
    },
    getDifference(paymentId) {
        if (this.state.payments[paymentId].counted.indexOf('.') >= 0 && this.state.payments[paymentId].counted.indexOf(',') == (-1)){
            this.state.payments[paymentId].counted = this.state.payments[paymentId].counted.replace('.',',');
        }
        var res = super.getDifference(paymentId);
        return res;
    },
    async closeSession() {
        this.pos._resetConnectedCashier();
        if (this.pos.config.customer_display_type === "proxy") {
            const proxyIP = this.pos.getDisplayDeviceIP();
            fetch(`${deduceUrl(proxyIP)}/hw_proxy/customer_facing_display`, {
                method: "POST",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ params: { action: "close" } }),
            }).catch(() => {
                console.log("Failed to send data to customer display");
            });
        }
        // If there are orders in the db left unsynced, we try to sync.
        const syncSuccess = await this.pos.push_orders_with_closing_popup();
        if (!syncSuccess) {
            return;
        }
        if (this.pos.config.cash_control) {
            const response = await this.pos.data.call(
                "pos.session",
                "post_closing_cash_details_payment_method",
                [this.pos.session.id],
                {
                    defaultCash: this.props.default_cash_details,
                    nonCashPaymentMethods: this.props.non_cash_payment_methods,
                    paymentsCountedCash: this.state.payments,
                }
            );

            if (!response.successful) {
                return this.handleClosingError(response);
            }
        }

        try {
            await this.pos.data.call("pos.session", "update_closing_control_state_session", [
                this.pos.session.id,
                this.state.notes,
            ]);
        } catch (error) {
            // We have to handle the error manually otherwise the validation check stops the script.
            // In case of "rescue session", we want to display the next popup with "handleClosingError".
            // FIXME
            if (!error.data && error.data.message !== "This session is already closed.") {
                throw error;
            }
        }

        try {
            const bankPaymentMethodDiffPairs = this.props.non_cash_payment_methods
                .filter((pm) => pm.type == "bank")
                .map((pm) => [pm.id, this.getDifference(pm.id)]);
            const response = await this.pos.data.call(
                "pos.session",
                "close_session_from_ui",
                [this.pos.session.id, bankPaymentMethodDiffPairs],
                {
                    context: {
                        login_number: odoo.login_number,
                    },
                }
            );
            if (!response.successful) {
                return this.handleClosingError(response);
            }
            localStorage.removeItem(`pos.session.${odoo.pos_config_id}`);
            location.reload();
        } catch (error) {
            if (error instanceof ConnectionLostError) {
                throw error;
            } else {
                await this.handleClosingControlError();
            }
        }
    }
    /*,
    autoFillCashCountNonDefaultCash(id) {
        console.log('autoFillCashCountNonDefaultCash-this: ', this);
        console.log('autoFillCashCountNonDefaultCash-props: ', this.props);
        console.log('autoFillCashCountNonDefaultCash-state: ', this.state);
        console.log('autoFillCashCountNonDefaultCash-id: ', id);
        var count = 0;
        for (var i = 0; i < this.props.non_cash_payment_methods.length; i++){
            if (this.props.non_cash_payment_methods[i].id == id){
                count = this.props.non_cash_payment_methods[i].amount;
            }
        }
        console.log('autoFillCashCountNonDefaultCash-count: ', count);
        console.log('autoFillCashCountNonDefaultCash-counted: ', this.state.payments[id].counted);
        this.state.payments[id].counted = this.env.utils.formatCurrency(count, false);
        this.setManualCashInput(count);
    }*/
});