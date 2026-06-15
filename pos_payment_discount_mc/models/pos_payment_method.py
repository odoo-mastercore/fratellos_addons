# -*- coding: utf-8 -*-
import pprint
from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    enable_discount = fields.Boolean("Habilitar descuento/recargo")
    discount_type = fields.Selection(selection=[
        ('discount', 'Descuento'),
        ('increase', 'Recargo')], string='Tipo de ajuste', default='discount',readonly=False)
    adjustment_product_id = fields.Many2one('product.product', string='Descripcion en pedido', require=True, domain="[]")
    rate_discount = fields.Float("Porcentaje")
    round_payment_amount = fields.Boolean("Redondear monto del pago", default=False)
    apply_discount_on_lines = fields.Boolean("Aplicar descuento en las lineas del pedido", default=True)
    apply_total_discount_with_differences_less_than = fields.Float("Diferencia maxima para descuento total", default=0.0)
    apply_discount_to_total_order = fields.Boolean("Aplicar en base al total del pedido", default=False)

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('enable_discount')
        res.append('discount_type')
        res.append('adjustment_product_id')
        res.append('rate_discount')
        res.append('round_payment_amount')
        res.append('apply_discount_on_lines')
        res.append('apply_total_discount_with_differences_less_than')
        res.append('apply_discount_to_total_order')
        return res