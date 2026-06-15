# -*- coding: utf-8 -*-
################################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
################################################################################
from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp

class PosSession(models.Model):
    _inherit = 'pos.session'

    def show_pos_access_history(self):
        return {
            'name': _('Historial de acceso en pos'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.access.history',
            'view_mode': 'list',
            'domain': [('session_id', '=', self.id)],
        }