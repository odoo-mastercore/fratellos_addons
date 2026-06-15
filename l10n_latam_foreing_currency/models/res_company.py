# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2021-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
from odoo import models, fields, _
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    foreign_currency_id = fields.Many2one('res.currency',
        string='Divisa', default=lambda x: x.env.ref('base.USD') or False
    )