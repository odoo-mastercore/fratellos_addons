# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2022-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    company_inter_sale_id = fields.Many2one('account.journal', string='Venta inter compañía',
                                         )
    company_inter_purchase_id = fields.Many2one('account.journal', string='Compra inter compañía')

    smart_projection_days = fields.Integer(string='Días a proyectar', default=15)
    smart_history_months = fields.Integer(string='Meses de historial', default=1)
