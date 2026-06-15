# -*- coding: utf-8 -*-
import pprint
from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    enable_currencies = fields.Boolean("Pago en Divisas")
    currency_id = fields.Many2one("res.currency", string='Tipo de moneda del método de pago', readonly=False, related='journal_id.currency_id')
    currency_idx = fields.Integer(string='Indice de moneda del método de pago', readonly=False, related='journal_id.currency_id.id')
    currency_rate = fields.Float(string='Tasa de cambio', related='journal_id.currency_id.rate')
    currency_symbol = fields.Char(related='journal_id.currency_id.symbol')
    currency_position = fields.Selection(related='journal_id.currency_id.position')
    currency_decimal_places = fields.Integer(related='journal_id.currency_id.decimal_places')
    currency_rounding = fields.Float(related='journal_id.currency_id.rounding')
    journal_idx = fields.Integer(string='Indice del diario', readonly=False, related='journal_id.id')
    format_currency = fields.Char(string='Formato de moneda', compute='_compute_format_currency')
    enable_payment_reference = fields.Boolean("Habilitar referencia en pagos")
    enable_payment_lot = fields.Boolean("Habilitar lote en pagos")
    enable_payment_terminal = fields.Boolean("Habilitar terminal en pagos")
    enable_commission = fields.Boolean("Habilitar comisión de pagos")
    rate_commission = fields.Float("Porcentaje de comisión")
    default_account_commission_id = fields.Many2one(comodel_name='account.account', check_company=True, copy=False, ondelete='restrict', string='Cuenta contable de comisión')
    enable_islr = fields.Boolean("Habilitar retención de ISLR")
    rate_islr = fields.Float("Porcentaje de retención de ISLR")
    default_account_islr_id = fields.Many2one(comodel_name='account.account', check_company=True, copy=False, ondelete='restrict', string='Cuenta contable de retención de ISLR')
    journal_type = fields.Selection('Tipo de diario del método de pago', related='journal_id.type')
    enable_amount_opening = fields.Boolean("Habilitar monto de apertura")
    amount_opening = fields.Float("Monto de apertura")
    show_currency_equivalence = fields.Boolean("Mostrar equivalencia en divisas", default=False)

    @api.onchange('enable_currencies')
    def _onchange_enable_currencies(self):
        for record in self:
            if (record.enable_currencies == True):
                record.show_currency_equivalence = False
                
    def _compute_format_currency(self):
        for pay in self:
            if (len(pay.currency_id) == 0 or pay.currency_id.id == self.env.company.currency_id.id):
                pay.format_currency = {
                    'symbol': self.env.company.currency_id.symbol,
                    'position': self.env.company.currency_id.position,
                    'rounding': self.env.company.currency_id.rounding,
                    'decimals': self.env.company.currency_id.decimal_places
                    }
            else:
                pay.format_currency = {
                    'symbol': pay.currency_id.symbol,
                    'position': pay.currency_id.position,
                    'rounding': pay.currency_id.rounding,
                    'decimals': pay.currency_id.decimal_places
                    }

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('journal_idx')
        res.append('enable_currencies')
        res.append('currency_idx')
        res.append('currency_symbol')
        res.append('currency_position')
        res.append('currency_decimal_places')
        res.append('currency_rounding')
        res.append('currency_rate')
        res.append('format_currency')
        res.append('enable_payment_reference')
        res.append('enable_payment_lot')
        res.append('enable_payment_terminal')
        res.append('journal_type')
        res.append('enable_amount_opening')
        res.append('amount_opening')
        res.append('show_currency_equivalence')
        return res