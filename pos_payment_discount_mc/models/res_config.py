# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import fields, models, tools, api
from odoo.modules.module import get_resource_path

class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    remove_payment_lines_modifying_order = fields.Boolean(string='Remover lineas de pago al modificar el pedido', related='pos_config_id.remove_payment_lines_modifying_order', readonly=False)