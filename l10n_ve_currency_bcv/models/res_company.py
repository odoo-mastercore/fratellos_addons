# -*- coding: utf-8 -*-
##############################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0) 
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
###############################################################################
from odoo import fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    currency_rate_bcv = fields.Boolean(string='Automatic Currency BCV')
    currency_available_ids = fields.Many2many(comodel_name='res.currency',
                                              string='Currencies Available', )
    block_days_bcv = fields.Boolean(string='Block days BCV', 
                                    default=False)
    days_bcv_ids = fields.Many2many(comodel_name='days.bcv', 
                                    relation='days_bcv_company_rel', 
                                    column1='company_id',
                                    column2='days_bcv_id', 
                                    string='Days')
    force_rate_all_currencys = fields.Boolean(string='Forzar la tasa de cambio de todas las moendas BCV', 
                                              default=False)
    force_currency_id = fields.Many2one(comodel_name='res.currency', 
                                        string='Moneda de la tasa forzada', 
                                        readonly=False)