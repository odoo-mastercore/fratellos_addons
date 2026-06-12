# -*- coding: utf-8 -*-
##############################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
#
###############################################################################
{
    'name': "Product Label DeTodo",
    'description': """
        Crea template de etiquetas para productos y permite imprimir etiquetas de productos con precios
    """,
    'author': 'Mastercore Sinapsys Global®',
    'website': 'https://www.mastercore.us',
    'license': 'OPL-1',
    'version': '18.0.0.4',
    'category': 'Stock',
    'depends': ['base', 'product', 'stock'],
    'data': [
        #'security/ir.model.access.csv',
        'report/report_label_detodo.xml',
        'report/report_paperformat.xml',
        'report/report_acctions.xml',
        'views/view_product_lspt.xml',
        'views/view_pricelist.xml'
        #'data/label_format_data.xml',
        #'wizard/wizard_views.xml',
        #'views/product_view.xml',
        #'views/res_company_view.xml',
    ],
}