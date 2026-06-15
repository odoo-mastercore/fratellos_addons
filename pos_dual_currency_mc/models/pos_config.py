# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from uuid import uuid4
import pytz

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

class PosConfig(models.Model):
    _inherit = "pos.config"

    show_dual_currency = fields.Boolean("Mostrar moneda secundaria", help="Mostrar moneda secundaria en POS", default=False)
    show_currency = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env['res.currency'].search([('id', '=', self.env.company.foreign_currency_id.id)], limit=1))
    show_currency_id = fields.Integer(string='Indice de moneda', related='show_currency.id')
    show_currency_rate = fields.Float(string='Tasa de cambio', related='show_currency.rate')
    show_currency_symbol = fields.Char(related='show_currency.symbol')
    show_currency_position = fields.Selection(related='show_currency.position')
    show_currency_decimal_places = fields.Integer(related='show_currency.decimal_places')
    show_currency_rounding = fields.Float(related='show_currency.rounding')
    show_currency_rate_date = fields.Date("Tasa del día", compute='_compute_show_currency_rate_date', compute_sudo=True, store=False, digits=0, readonly=True, help='Tasa del día')
    last_session_closing_cash_other = fields.Char(string="Útimo cierre de sesión efectivo", compute='_compute_last_session', store=False)
    #calculation_operation = fields.Selection(selection=[
        #('*', 'Multiplication'),
        #('/', 'Division')], string='Calculation operation', readonly=False)
    opening_cash_mode = fields.Selection(selection=[
        ('last_opening', 'Última apertura'),
        ('no_values', 'Sin valores (0,00)'),
        ('setting_amount', 'Cantidad establecida por el usuario')], default='last_opening', string='Modo apertura del efectivo', readonly=False)
    #hide_detail_kanban = fields.Boolean(string='Ocultar detalle en la vista Kanban de la caja', default=False)
    last_session_rate = fields.Monetary(currency_field='currency_id', compute='_compute_last_session', store=False)
    last_session_date_rate = fields.Date(compute='_compute_last_session', store=False)
    enable_popup_references_payment = fields.Boolean(string='Habilitar ventanas emergentes para referencias de pagos.', default=False)
    disabled_print_invoice = fields.Boolean(string='Inhabilitar impresion de factura automatica.', default=False)
    forced_button_invoice = fields.Boolean("Forzar de boton de factura, en la generacion de pedidos del Pos.", help="Habilitar ventanas emergentes para referencias de pagos.", default=False)
    #disabled_pricelist_bottom = fields.Boolean(string='Deshabilitar boton de tarifas en el POS.', default=True)
    clear_search_adding_product = fields.Boolean(string='Limpiar buscador despues de agregar productos.', default=True)
    hide_exchange_rate_pos = fields.Boolean(string='Ocultar tasa de cambio en POS.', default=False)
    enable_automatic_box_opening = fields.Boolean(string='Habilitar apertura de caja automatica.', default=False)
    #hide_button_orders = fields.Boolean(string='Ocultar boton de pedidos en POS.', default=False)
    assign_customer_account_zero_making_order_payments = fields.Boolean("Asignar la cuenta del cliente a cero para realizar pagos de pedidos", default=True)
    view_payments_journal_currency = fields.Boolean(string='Visualizar pagos del recibo en la moneda del diario.')
    view_quantity_products = fields.Boolean(string='Indicador de cantidad de productos.', default=True)
    #hide_symbol_currency = fields.Boolean("Ocultar simbolo de moneda en POS", help="Hide Symbol Currency in POS", default=False)

    def _compute_show_currency_rate_date(self):
        self.show_currency_rate_date = self.show_currency.rate_ids[:1].name

    @api.depends('session_ids')
    def _compute_last_session(self):
        PosSession = self.env['pos.session']
        for pos_config in self:
            session = PosSession.search_read(
                [('config_id', '=', pos_config.id), ('state', '=', 'closed')],
                ['cash_register_balance_end_real', 'stop_at', 'start_at'], #, 'cash_register_id'
                order="stop_at desc", limit=1)
            if session:
                accountBankStatement = self.env['account.bank.statement'].sudo().search([('pos_session_id', '=', session[0]['id'])],order='name desc')
                timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
                pos_config.last_session_closing_date = session[0]['stop_at'].astimezone(timezone).date()
                pos_config.last_session_date_rate = session[0]['start_at'].astimezone(timezone).date()
                pos_config.last_session_closing_cash = 0
                pos_config.last_session_closing_cash_other = ((pos_config.show_currency.symbol + ' ' + '0,00') if (pos_config.show_currency.position == 'before') else ('0,00' + " " + pos_config.show_currency.symbol) if (len(pos_config.show_currency) > 0) else '0,00')
                for bankStatement in accountBankStatement:
                    #if ((len(bankStatement.journal_id.currency_id) == 0) or (bankStatement.journal_id.currency_id.id == self.env.company.currency_id.id)):
                    if (len(bankStatement.currency_id) == 0 or (bankStatement.currency_id.id == self.env.company.currency_id.id)):
                        pos_config.last_session_closing_cash = bankStatement.balance_end_real
                    else:
                        pos_config.last_session_closing_cash_other = (bankStatement.payment_method_id.journal_id.currency_id.symbol + ' ' + str(bankStatement.balance_end_real)) if (bankStatement.payment_method_id.journal_id.currency_id.position == 'before') else (str(bankStatement.balance_end_real) + " " + bankStatement.payment_method_id.journal_id.currency_id.symbol)
                cur_rate = self.env['res.currency.rate'].search([('name', '<=', session[0]['start_at'].astimezone(timezone).date()), ('company_id', '=', pos_config.company_id.id), ('currency_id', '=', pos_config.show_currency.id)], limit=1)
                if (len(cur_rate) > 0):
                    pos_config.last_session_rate = round((1 / cur_rate.rate), 2)
                else:
                    pos_config.last_session_rate = 0.0
            else:
                pos_config.last_session_closing_cash = 0
                pos_config.last_session_closing_cash_other = ((pos_config.show_currency.symbol + ' ' + '0,00') if (pos_config.show_currency.position == 'before') else ('0,00' + " " + pos_config.show_currency.symbol) if (len(pos_config.show_currency) > 0) else '0,00')
                pos_config.last_session_closing_date = False
                pos_config.last_session_date_rate = False
                pos_config.last_session_rate = 0.0

    def get_calculate_other_rate(self, date):
        c_rate = self.env['res.currency.rate'].search([('currency_id', '=', self.show_currency.id), ('company_id', '=', self.company_id.id),
                ('name', '<=', date)], order='name desc', limit=1) #date
        if (len(c_rate) > 0):
            return {
                'show_currency_rate': c_rate[0].rate,
                'show_currency_rate_date': c_rate[0].name,
            }
        else:
            return {
                'show_currency_rate': self.show_currency_rate,
                'show_currency_rate_date': self.show_currency_rate_date,
            }

    @api.constrains('pricelist_id', 'use_pricelist', 'available_pricelist_ids', 'journal_id', 'invoice_journal_id', 'payment_method_ids')
    def _check_currencies(self):
        for config in self:
            if config.use_pricelist and config.pricelist_id and config.pricelist_id not in config.available_pricelist_ids:
                raise ValidationError(_("The default pricelist must be included in the available pricelists."))
            # Check if the config's payment methods are compatible with its currency
            #for pm in config.payment_method_ids:
                #if pm.journal_id and pm.journal_id.currency_id and pm.journal_id.currency_id != config.currency_id:
                    #raise ValidationError(_("All payment methods must be in the same currency as the Sales Journal or the company currency if that is not set."))
            if config.use_pricelist and any(config.available_pricelist_ids.mapped(lambda pricelist: pricelist.currency_id != config.currency_id)):
                raise ValidationError(_("All available pricelists must be in the same currency as the company or"
                                        " as the Sales Journal set on this point of sale if you use"
                                        " the Accounting application."))
            if config.invoice_journal_id.currency_id and config.invoice_journal_id.currency_id != config.currency_id:
                raise ValidationError(_("The invoice journal must be in the same currency as the Sales Journal or the company currency if that is not set."))