# -*- coding: utf-8 -*-
################################################################################
# Author      : SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyright(c): 2025-Present.
# License URL : AGPL-3
#
################################################################################
from odoo import fields, models, _
import logging
_logger = logging.getLogger(__name__)


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    enable_secondary_tariff  = fields.Boolean(
        string='Habilitar Tarifa Secundaria para Referencia',
        default=False
    )
