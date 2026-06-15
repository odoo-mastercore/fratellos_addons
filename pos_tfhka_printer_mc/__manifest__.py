# -*- coding: utf-8 -*-
################################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
################################################################################
{
    "name": "Pos TFHKA printer Integration Mastercore",
    "version": "18.0.0.0.0",
    "description": """
        Pos TFHKA printer Integration Mastercore.
    """,
    "summary": """""",
    "category": "Point Of Sale",
    'license': 'AGPL-3',
    'author': "SINAPSYS GLOBAL SA || MASTERCORE SAS",
    'sequence': 1,
    'website': "http://sinapsys.global",
    "depends": ["base", "point_of_sale", "pos_payment_discount_mc", "account"],
    "data": [
        "views/views.xml",
        "views/menu_views.xml",
        'wizard/tfhka_fiscal_info.xml',
        'security/ir.model.access.csv',
    ],
    #"qweb": ["static/src/xml/pos.xml"],
    'assets': {
        'point_of_sale.assets': [
            'pos_tfhka_printer_mc/static/src/lib/crypto-js/crypto-js.min.js',
        ],
        'web.assets_qweb': [
            #'pos_tfhka_printer_mc/static/src/xml/**',
        ],
        'point_of_sale._assets_pos': [
            'pos_tfhka_printer_mc/static/src/app/store/**/*',#.js
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}