# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class PosOrderReport(models.Model):
    _inherit = "report.pos.order"

    price_subtotal_foreign = fields.Float(string='Subtotal sin descuento (M2)', readonly=True)
    price_total_foreign = fields.Float(string='Precio Total (M2)', readonly=True)
    average_price_foreign = fields.Float(string='Precio medio (M2)', readonly=True, group_operator="avg")

    def _select(self):
        res = super()._select()
        res = res + """, SUM(l.price_subtotal_foreign) AS price_subtotal_foreign, SUM(l.price_subtotal_incl_foreign) AS price_total_foreign, CASE
                    WHEN SUM(l.qty * u.factor) = 0 THEN NULL
                    ELSE (SUM(l.qty*l.price_unit_foreign)/SUM(l.qty * u.factor))::decimal
                END AS average_price_foreign """
        return res