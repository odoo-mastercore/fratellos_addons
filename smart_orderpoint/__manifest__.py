# -*- coding: utf-8 -*-
##############################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2021-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
###############################################################################
{
    'name': "Smart Orderpoint",
    'version': "18.0.1.0.1",
    'summary': "Enhance stock reordering rules with sales/purchase history and inter‑company options",
    'category': 'Inventory/Inventory',
    'author': "Mastercore Sinapsys Global®",
    'license': 'OPL-1',
    'depends': [
        'stock',
        'purchase_stock',
        'sale_stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/smart_orderpoint_cron.xml',
        'views/stock_warehouse_orderpoint_views.xml',
        'views/smart_onderpoint_views.xml',
        'views/res_config_settings_views.xml',
        #'views/wizard_stock_wh_orderpoint_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
