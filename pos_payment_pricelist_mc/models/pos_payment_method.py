# -*- coding: utf-8 -*-
import pprint
from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    disabled_exclusive_currency_in_pricelist = fields.Boolean("Deshabilitar metodo de pago para tarifas exclusivas de la moneda de la tarifa")
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('disabled_exclusive_currency_in_pricelist')
        return res