# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2022-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    # def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
    #     res = super()._update_purchase_order_line(product_id, product_qty, product_uom, company_id, values, line)
    #     if (values['orderpoint_id']):
    #         orderpoint_id = values['orderpoint_id']
    #         res['price_unit'] = orderpoint_id.purchase_price or orderpoint_id.purchased_price
    #         if (values['orderpoint_id'].product_id.uom_id.id != values['orderpoint_id'].product_id.uom_po_id.id):
    #             res['product_qty'] = values['orderpoint_id'].qty_to_order_uom
    #         else:
    #             res['product_qty'] = values['orderpoint_id'].qty_to_order
    #     return res


    def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        vals = super()._update_purchase_order_line(product_id, product_qty, product_uom, company_id, values, line)
        if values.get('purchase_price') is not None:
            vals['price_unit'] = values['purchase_price']
        return vals

    def _make_po_get_domain(self, company_id, values, partner):
        """En SmartPro, usa dominio canónico para agrupar líneas en una sola OC."""
        domain = super()._make_po_get_domain(company_id, values, partner)
        orderpoint = values.get('orderpoint_id')
        if not orderpoint or orderpoint.trigger != 'smartpro':
            return domain

        supplier = values.get('supplier')
        currency = (supplier and supplier.currency_id) or partner.with_company(company_id).property_purchase_currency_id or company_id.currency_id
        return (
            ('partner_id', '=', partner.id),
            ('state', '=', 'draft'),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('company_id', '=', company_id.id),
            ('currency_id', '=', currency.id),
        )
