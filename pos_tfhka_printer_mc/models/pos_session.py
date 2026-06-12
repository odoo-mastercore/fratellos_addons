# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2020-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class PosSession(models.Model):
    _inherit = 'pos.session'

    fiscal_report_z_id = fields.One2many('fiscal.report.z', 'pos_session_id', string='Reporte Z')
    is_tax_box = fields.Boolean('Caja fiscal', readonly=False, related='config_id.is_tax_box')

    def show_fiscal_report_z(self):
        return {
            'name': _('Reporte Z'),
            'type': 'ir.actions.act_window',
            'res_model': 'fiscal.report.z',
            'view_mode': 'list',
            'domain': [('pos_session_id', '=', self.id)],
        }