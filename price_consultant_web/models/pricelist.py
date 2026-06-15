# -*- coding: utf-8 -*-
################################################################################
# Author      : SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyright(c): 2022-Present.
# License URL : AGPL-3
#
################################################################################
from odoo import fields, models, _
import logging
_logger = logging.getLogger(__name__)


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    enabled_price_consultant = fields.Boolean(
        string='Habilitar en Consultor de Precios',
        default=False
    )
