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
    'name': "Visualizacion de precio total en los productos (Base+IVA)",
    'description': """
    """,
    'author': 'Mastercore Sinapsys Global®',
    'website': 'https://www.mastercore.us',
    'license': 'OPL-1',
    'version': '18.0.0.0',
    'category': 'stock',
    'depends': ['product', 'stock', 'account'],
    'data': [
        'views/views.xml',
    ],
}