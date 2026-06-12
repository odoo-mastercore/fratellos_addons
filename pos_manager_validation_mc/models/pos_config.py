# -*- coding: utf-8 -*-
################################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
################################################################################
from datetime import datetime
from uuid import uuid4
import pytz

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

class PosConfig(models.Model):
    _inherit = 'pos.config'

    close_pos = fields.Boolean(string='Cerra caja registradora')
    order_delete = fields.Boolean(string='Eliminar orden')
    order_line_delete = fields.Boolean(string='Eliminar linea de la orden')
    qty_detail = fields.Boolean(string='Agregar/Remover cantidad')
    discount_app = fields.Boolean(string='Aplicar descuento')
    disabled_discount_app = fields.Boolean(string='Deshabilitar descuento')
    payment_perm = fields.Boolean(string='Pagos')
    price_change = fields.Boolean(string='Cambio de precio')
    disabled_price_change = fields.Boolean(string='Deshabilitar cambio de precio')
    move_in_out_cash = fields.Boolean(string='Entrada/Salida de efectivo')
    restrict_pos_product_category_active = fields.Boolean(string='Restringir categorias de productos')
    pos_product_category_restrict_ids = fields.Many2many('pos.category', 'pos_category_restrict_rel',
        'pos_config_id', 'pos_category_id', string='Categorias de productos')
    restrict_cash_opening = fields.Boolean(string='Restringir apertura de caja solo a usuarios supervisores')
    restrict_pos_payment_method_active = fields.Boolean(string='Restringir metodos de pago')
    pos_payment_method_restrict_ids = fields.Many2many('pos.payment.method', 'pos_payment_method_restrict_rel',
        'pos_config_id', 'pos_payment_method_id', string='Metodos de pago')
    return_orders = fields.Boolean(string='Devoluciones de pedidos')
    set_fiscal_position = fields.Boolean(string='Posicion fiscal')
    set_pricelist_product = fields.Boolean(string='Cambio de tarifas')
    hide_pricelist_foreign_currency = fields.Boolean(string='Ocultar tarifas en divisas')