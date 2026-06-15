# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2021-Present.
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

    list_price_total = fields.Monetary(string="Precio de venta + IVA", compute="_compute_list_price_total")

    @api.depends('list_price', 'taxes_id')
    def _compute_list_price_total(self):
        for rec in self:
            rec.list_price_total = rec.taxes_id.compute_all(rec.list_price)['total_included']

class ProductProduct(models.Model):
    _inherit = "product.product"

    list_price_total = fields.Monetary(string="Precio de venta + IVA", compute="_compute_list_price_total")

    @api.depends('list_price', 'taxes_id')
    def _compute_list_price_total(self):
        for rec in self:
            rec.list_price_total = rec.taxes_id.compute_all(rec.list_price)['total_included']