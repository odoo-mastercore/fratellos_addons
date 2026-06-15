# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import fields, models, tools, api
from odoo.modules.module import get_resource_path

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    pos_payment_method_id = fields.Many2one('pos.payment.method', string='Método de pago caja registradora en TPV')