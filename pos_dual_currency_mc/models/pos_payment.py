# -*- coding: utf-8 -*-
import pprint
from odoo import api, fields, models, _
from odoo.tools import formatLang, float_is_zero
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class PosPayment(models.Model):
    _inherit="pos.payment"

    pay_currency_id = fields.Many2one("res.currency", related="payment_method_id.journal_id.currency_id", string="Divisas")
    amount_foreign = fields.Monetary("Importe en Divisas", currency_field='pay_currency_id')
    payment_reference = fields.Char('Referencia del pago')
    payment_lot = fields.Char('Lote del pago')
    payment_terminal = fields.Char('Terminal del pago')
    state = fields.Selection([('draft', 'New'),
         ('cancel', 'Cancelled'),
         ('paid', 'Paid'),
         ('done', 'Posted'),
         ('invoiced', 'Invoiced')], 'Estado', readonly=False, related='pos_order_id.state')
    currency_rate_foreign = fields.Float("Tasa de cambio", digits=(16, 4), readonly=True, currency_field='pay_currency_id', help='El tipo de cambio de la moneda a la correspondiente al medio de pago.')