# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import fields, models, tools, api, _
from odoo.tools import formatLang, float_is_zero
from odoo.modules.module import get_resource_path
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang
import logging
_logger = logging.getLogger(__name__)

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    company_foreign_currency_id = fields.Many2one('res.currency', string='Moneda extranjera', readonly=True,related='company_id.foreign_currency_id')
    price_unit_foreign = fields.Monetary(string='Precio unitario (Divisa)', readonly=True, currency_field='company_foreign_currency_id')
    price_subtotal_foreign = fields.Monetary(string='Subtotal neto (Divisa)', readonly=True, currency_field='company_foreign_currency_id')
    price_subtotal_incl_foreign = fields.Monetary(string='Subtotal (Divisa)', readonly=True, currency_field='company_foreign_currency_id')
	#fiscal_invoice_number = fields.Char(string='Nro Doc Venta', related='order_id.fiscal_invoice_number', readonly=True)
    config_id = fields.Many2one('pos.config', string='TPV', readonly=True, related='order_id.config_id')
    #employee_id = fields.Many2one('hr.employee', string='Cajero', readonly=True, related='order_id.employee_id')
    default_code = fields.Char(string='Cod Produ', related='product_id.default_code', readonly=True)
    categ_id = fields.Many2one('product.category', string='Categoria Prod', readonly=True, related='product_id.categ_id')

    def _prepare_refund_data(self, refund_order, PosOrderLineLot):
        res = super()._prepare_refund_data(refund_order, PosOrderLineLot)
        res['price_unit_foreign'] = -self.price_unit_foreign
        res['price_subtotal_foreign'] = -self.price_subtotal_foreign
        res['price_subtotal_incl_foreign'] = -self.price_subtotal_incl_foreign
        return res

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('company_foreign_currency_id')
        res.append('price_unit_foreign')
        res.append('price_subtotal_foreign')
        res.append('price_subtotal_incl_foreign')
        return res