# -*- coding: utf-8 -*-
##############################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0) 
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
###############################################################################
from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    currency_rate_bcv = fields.Boolean(string='Automatic Currency BCV',
                                       related='company_id.currency_rate_bcv', 
                                       readonly=False,)
    currency_available_ids = fields.Many2many(comodel_name='res.currency',
                                              string='Currencies Available (BCV)', 
                                              readonly=False,
                                              related='company_id.currency_available_ids', )
    block_days_bcv = fields.Boolean(string='Block days BCV',
                                    related='company_id.block_days_bcv', 
                                    readonly=False)
    days_bcv_ids = fields.Many2many(comodel_name='days.bcv',
                                    string='Days',
                                    related='company_id.days_bcv_ids',
                                    readonly=False)
    force_rate_all_currencys = fields.Boolean(string='Forzar la tasa de cambio de todas las moendas BCV', 
                                              readonly=False, 
                                              related='company_id.force_rate_all_currencys')
    force_currency_id = fields.Many2one(comodel_name='res.currency', 
                                        string='Moneda de la tasa forzada', 
                                        readonly=False, 
                                        related='company_id.force_currency_id')