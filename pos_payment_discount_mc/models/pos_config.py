# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from uuid import uuid4
import pytz

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

class PosConfig(models.Model):
    _inherit = "pos.config"

    remove_payment_lines_modifying_order = fields.Boolean(string='Remover lineas de pago al modificar el pedido')