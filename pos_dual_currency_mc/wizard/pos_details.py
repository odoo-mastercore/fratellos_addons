# -*- coding: utf-8 -*-
################################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'

    only_payment_details = fields.Boolean(string='Solo informacion del pago.', default=True)

    @api.onchange('search_type')
    def _onchange_start_date(self):
        super._onchange_start_date()
        self.only_payment_details = True

    def generate_report(self):
        data = {'date_start': self.start_date, 'date_stop': self.end_date, 'config_ids': self.pos_config_ids.ids, 'only_payment_details': self.only_payment_details}
        return self.env.ref('point_of_sale.sale_details_report').report_action([], data=data)