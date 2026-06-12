# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import fields, models, tools, api
from odoo.modules.module import get_resource_path

class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    show_dual_currency = fields.Boolean("Mostrar moneda secundaria", help="Mostrar moneda secundaria en POS", readonly=False, related='pos_config_id.show_dual_currency')
    show_currency = fields.Many2one('res.currency', string='Moneda', readonly=False, related='pos_config_id.show_currency')
    #calculation_operation = fields.Selection(selection=[ 
        #('*', 'Multiplication'),
        #('/', 'Division')], string='Calculation operation', readonly=False, related='pos_config_id.calculation_operation')
    opening_cash_mode = fields.Selection(selection=[ 
        ('last_opening', 'Last opening'),
        ('no_values', 'No defaults'),
        ('setting_amount', 'Amount set by user')], string='Modo apertura del efectivo', readonly=False, related='pos_config_id.opening_cash_mode')
    #hide_detail_kanban = fields.Boolean(string='Ocultar detalle en la vista Kanban de la caja.', readonly=False, related='pos_config_id.hide_detail_kanban')
    enable_popup_references_payment = fields.Boolean(string='Habilitar ventanas emergentes para referencias de pagos.', readonly=False, related='pos_config_id.enable_popup_references_payment')
    forced_button_invoice = fields.Boolean("Forzar de boton de factura, en la generacion de pedidos del Pos.", help="Habilitar ventanas emergentes para referencias de pagos.", readonly=False, related='pos_config_id.forced_button_invoice')
    disabled_print_invoice = fields.Boolean(string='Inhabilitar impresion de factura automatica.', readonly=False, related='pos_config_id.disabled_print_invoice')
    #disabled_pricelist_bottom = fields.Boolean(string='Deshabilitar boton de tarifas en el POS.', readonly=False, related='pos_config_id.disabled_pricelist_bottom')
    clear_search_adding_product = fields.Boolean(string='Limpiar buscador despues de agregar productos.', readonly=False, related='pos_config_id.clear_search_adding_product')
    hide_exchange_rate_pos = fields.Boolean(string='Ocultar tasa de cambio en POS.', readonly=False, related='pos_config_id.hide_exchange_rate_pos')
    enable_automatic_box_opening = fields.Boolean(string='Habilitar apertura de caja automatica.', readonly=False, related='pos_config_id.enable_automatic_box_opening')
    view_quantity_products = fields.Boolean(string='Indicador de cantidad de productos.', readonly=False, related='pos_config_id.view_quantity_products')
    #hide_button_orders = fields.Boolean(string='Ocultar boton de pedidos en POS.', readonly=False, related='pos_config_id.hide_button_orders')