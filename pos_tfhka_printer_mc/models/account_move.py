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

class AccountMove(models.Model):
    _inherit = 'account.move'

    fiscal_invoice_number = fields.Char(string='Número de factura fiscal', help="Fiscal invoice number issued by TFHKA.")
    printer_serial = fields.Char(string='Serial de la impresora', readonly=False, help="Printer serial by TFHKA.")

    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft)
        return res