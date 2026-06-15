# -*- coding: utf-8 -*-
##############################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2021-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    include_orderpoint = fields.Boolean(
        string='Incluido en Smart Orderpoint',
        default=False,
        help='Si está activo, el cron de Smart Orderpoint generará/validará '
             'la regla de reabastecimiento para este producto.',
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    include_orderpoint = fields.Boolean(
        related='product_tmpl_id.include_orderpoint',
        store=True,
        readonly=False,
    )

