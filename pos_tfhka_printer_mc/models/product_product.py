# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2022-Present.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import hashlib

class ProductProduct(models.Model):
    _inherit = 'product.product'

    tax_amount = fields.Float('Importe del impuesto', related='taxes_id.amount')
    ignore_send_fiscal_printer = fields.Boolean('No enviar a impresora fiscal TFHKA', readonly=False, related='product_tmpl_id.ignore_send_fiscal_printer')

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('tax_amount')
        res.append('ignore_send_fiscal_printer')
        return res

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ignore_send_fiscal_printer = fields.Boolean('No enviar a impresora fiscal TFHKA', default=False)