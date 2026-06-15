# -*- coding: utf-8 -*-
################################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
################################################################################
{
    "name": "POS Manager Validation Mastercore",
    "version": "18.0.0.0.0",
    "description": """
        POS Manager Validation Mastercore.
    """,
    "summary": """""",
    "category": "Point Of Sale",
    'license': 'AGPL-3',
    'author': "SINAPSYS GLOBAL SA || MASTERCORE SAS",
    'sequence': 1,
    'website': "http://sinapsys.global",
    "depends": ["base", "point_of_sale", "stock", "account", "pos_settle_due", "pos_hr"],
    "data": [
        "views/views.xml",
        'security/ir.model.access.csv',
    ],
    #"qweb": ["static/src/xml/pos.xml"],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_manager_validation_mc/static/src/app/store/**/*',#.js
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}