# -*- coding: utf-8 -*-
##############################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0) 
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
###############################################################################
from odoo import fields, models, _


class BankHolidaysBcv(models.Model):
    _name = 'bank.holidays.bcv'

    name = fields.Char(string='Description')
    date = fields.Date(
        string='Bank holidays',
        default=fields.Date.context_today,
    )

    
class DaysBcv(models.Model):
    _name = 'days.bcv'

    code = fields.Integer(string='Code')
    name = fields.Char(string='Name')