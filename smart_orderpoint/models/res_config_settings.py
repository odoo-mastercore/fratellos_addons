# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2022-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_inter_sale_id = fields.Many2one('account.journal', 
                                            string='Venta inter compañía',
                                            related='company_id.company_inter_sale_id',
                                            readonly=False,)
    company_inter_purchase_id = fields.Many2one('account.journal', 
                                                string='Compra inter compañía',
                                                related='company_id.company_inter_purchase_id',
                                                readonly=False,)

    smart_projection_days = fields.Integer(string='Días a proyectar',
                                           related='company_id.smart_projection_days',
                                           readonly=False)
    smart_history_months = fields.Integer(string='Meses de historial',
                                          related='company_id.smart_history_months',
                                          readonly=False)
