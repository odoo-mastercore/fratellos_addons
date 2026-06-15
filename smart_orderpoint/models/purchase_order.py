# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2022-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################

from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    company_inter = fields.Boolean(string='Inter compañía', default=False)


    def _prepare_invoice(self):
        invoice_dict = super(PurchaseOrder, self)._prepare_invoice()
        if self.company_inter:
            invoice_dict.update({'journal_id':self.company_id.company_inter_purchase_id.id})
        print(invoice_dict)
        return invoice_dict


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _prepare_purchase_order_line_from_procurement(
        self, product_id, product_qty, product_uom, location_dest_id,
        name, origin, company_id, values, po
    ):
        vals = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, location_dest_id,
            name, origin, company_id, values, po
        )
        if values.get('purchase_price') is not None:
            vals['price_unit'] = values['purchase_price']
        return vals
