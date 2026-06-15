# -*- coding: utf-8 -*-
################################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
################################################################################
from odoo import models, fields, api, _
from email.policy import default
from itertools import product

class PosAccessHistory(models.Model):
    _name = 'pos.access.history'
    _description = 'Historial de acceso en pos'

    name = fields.Selection(
        selection=[
            ('close_pos', 'Cierre de punto de venta'),
            ('order_delete', 'Eliminación de pedidos'),
            ('order_line_delete', 'Eliminación de línea de pedido'),
            ('qty_detail', 'Agregar/eliminar cantidad'),
            ('discount_app', 'Aplicar descuento'),
            ('payment_perm', 'Pago'),
            ('price_change', 'Cambio de precio'),
            ('move_in_out_cash', 'Entrada/Salida de efectivo'),
            ('restrict_pos_product_category', 'Carga de producto restringido'),
            ('restrict_pos_payment_method', 'Restringir metodos de pago'),
            ('return_orders', 'Devoluciones de pedidos'),
            ('set_fiscal_position', 'Posicion fiscal'),
            ('set_pricelist_product', 'Cambio de tarifa'),
        ], string="Accion", readonly=True)
    session_id = fields.Many2one(
        'pos.session', string='Sesion', required=True, index=True,
        domain="[('state', '=', 'opened')]", states={'draft': [('readonly', False)]},
        readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Supervisor')
    state = fields.Selection(
        selection=[
            ('fail', 'Fallida'),
            ('successful', 'Exitosa'),
        ], string='Estado')
    pos_category_id = fields.Many2one('pos.category', string='Categoria del producto')
    product_id = fields.Many2one('product.product', string='Producto')
    pos_payment_method_id = fields.Many2one('pos.payment.method', string='Metodo de pago')
    pos_order_id = fields.Many2one('pos.order', string='Pedido')
    partner_id = fields.Many2one('res.partner', string='Cliente')

    @api.model
    def create_from_ui(self, access):
        pos_access = self.create(access)
        return pos_access