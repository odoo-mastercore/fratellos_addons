# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2022-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
from odoo import api, fields, models,_


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    company_inter = fields.Boolean(string='Inter compañía', default=False)
    
    
    def _prepare_invoice(self):
        invoice_dict = super(SaleOrder, self)._prepare_invoice()
        if self.company_inter:
            invoice_dict.update({'journal_id':self.company_id.company_inter_sale_id.id})
        return invoice_dict