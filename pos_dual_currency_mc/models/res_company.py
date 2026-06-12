# -*- coding: utf-8 -*-
import pprint
from odoo import api, models, fields

class PosSession(models.Model):
    _inherit = 'res.company'

    include_order_details_in_pos_detail_report = fields.Boolean(string='Incluir detalle de pedidos en reporte de detalle de ventas pos', default=False)
    foreign_currency_id = fields.Many2one('res.currency', string='Divisa', readonly=False)

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('foreign_currency_id')
        return res