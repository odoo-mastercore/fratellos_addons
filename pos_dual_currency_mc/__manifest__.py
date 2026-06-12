# -*- coding: utf-8 -*-
################################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
################################################################################
{
    "name": "POS Multi Currency Mastercore",
    "version": "18.0.0.0.0",
    "description": """
        Multi Currency Mastercore.
    """,
    "summary": """""",
    "category": "Point Of Sale",
    'license': 'AGPL-3',
    'author': "SINAPSYS GLOBAL SA || MASTERCORE SAS",
    'sequence': 1,
    'website': "http://sinapsys.global",
    "depends": ["base", "point_of_sale", "stock", "account", "pos_settle_due"],
    "data": [
        "views/views.xml",
        "wizard/pos_details.xml",
        #'security/ir.model.access.csv',
    ],
    #"qweb": ["static/src/xml/pos.xml"],
    'assets': {
        'point_of_sale.assets': [
            #'pos_dual_currency_mc/static/src/css/pos.css',
            #'pos_dual_currency_mc/static/src/js/**/*',
        ],
        'web.assets_qweb': [
            #'pos_dual_currency_mc/static/src/xml/**',
        ],
        'point_of_sale._assets_pos': [
            'pos_dual_currency_mc/static/src/app/store/**/*',#.js
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}