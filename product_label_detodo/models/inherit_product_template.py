# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2025-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    list_secondary_price_total = fields.Monetary(
        string="Precio total de tarifa secundaria + IVA",
        compute="_compute_secondary_price_total"
    )

    # Calcular Tarifa Secundaria (Product.Template)
    @api.depends('taxes_id')
    def _compute_secondary_price_total(self):
        for rec in self:
            item = self.env['product.pricelist.item'].search([
                ('product_tmpl_id', '=', rec.id),
                ('pricelist_id.enable_secondary_tariff', '=', True)
            ], limit=1)

            if item and item.fixed_price:
                rec.list_secondary_price_total = rec.taxes_id.compute_all(item.fixed_price)['total_included']
            else:
                rec.list_secondary_price_total = 0.0
