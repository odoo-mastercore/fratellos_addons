# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import fields, models, tools, api, _
from odoo.modules.module import get_resource_path
from odoo.exceptions import UserError, ValidationError

class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_lot = fields.Char('Lote del pago')
    payment_reference = fields.Char('Referencia del pago')
    payment_terminal = fields.Char('Terminal del pago')