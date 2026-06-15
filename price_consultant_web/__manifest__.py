# -*- coding: utf-8 -*-
###############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2020-Present.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
{
    "name": "Consultor de Precios - Website",
    "version": "18.0.1.0.2",
    "summary": "Price Consultant Web",
    "author": "SINAPSYS GLOBAL SA || MASTERCORE SAS",
    "license": "AGPL-3",
    "category": "Website",
    "depends": [
        'base',
        'sale_management', # For Pricelist menu
        'product',
        'l10n_latam_foreing_currency',
    ],
    "data": [
        "views/pricelist.xml",
        "views/consultant.xml"
    ],
    'assets': {
        'web.assets_frontend':[
            '/price_consultant_web/static/src/scss/consultant.scss',
            '/price_consultant_web/static/src/components/js/runtime.min.js',
            '/price_consultant_web/static/src/components/js/vendors.min.js',
            '/price_consultant_web/static/src/components/js/main.min.js'
        ]
    },
    "auto_install": False,
    "installable": True,
}
