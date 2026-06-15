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
    'name': "Actualizacion Monedas BCV",
    'description': """
        **Localización VENEZUELA**

        ¡Felicidades!. Este es el módulo Base para la implementación de la
        **Localización Venezuela** que extiende algunos modelos base de Odoo
        relacionados a la actualizacion de la moneda al cambio oficial de BCV.
    """,
    'author': 'Mastercore Sinapsys Global®',
    'website': 'https://www.mastercore.us',
    'license': 'OPL-1',
    'version': '18.0.0.0',
    'category': 'Localization',
    'depends': ['l10n_ve',],
    'data': [
        'security/ir.model.access.csv',
        'data/days_bcv.xml',
        'data/currency_rate_cron.xml',
        'views/bank_holidays.xml',
        'views/res_config_settings_views.xml',
    ],
}