# -*- coding: utf-8 -*-
import pprint
from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    enable_payment_exclusive_currency = fields.Boolean("Permitir pagos exclusivos en la moneda de la tarifa", default=False)

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('currency_id')
        res.append('enable_payment_exclusive_currency')
        return res