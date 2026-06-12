# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import fields, models, tools, api, _
from odoo.tools import formatLang, float_is_zero
from odoo.modules.module import get_resource_path
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang
import logging
_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = "pos.order"

    order_credit = fields.Selection(selection=[
        ('sales_refunds', 'Factura/Nota de Credito'),
        ('credit_sales', 'Factura a credito'),
        ('payment_contributions', 'Aportes de pago')], string="Tipo de Pedidos", compute='_compute_order_credit', compute_sudo=True, store=True, readonly=True, default='sales_refunds', help='Pedidos a credito')
    reason_for_cancellation = fields.Char('Motivo de cancelación', tracking=True)
    show_reason_for_cancellation = fields.Boolean('Visualizar Cancelacion de aportes de pago', compute='_compute_show_reason_for_cancellation')
    currency_rate_foreign = fields.Float("Tasa de cambio", digits=(16, 4), readonly=True, currency_field='company_foreign_currency_id', help='El tipo de cambio de la moneda a la fecha del pedido')
    pay_amount_foreign = fields.Float("Pagos en Divisas", compute='_compute_payments_currency', compute_sudo=True, store=False, digits=(16, 4), readonly=True, help='Payments USD')
    pay_amount_cur = fields.Float("Pagos", compute='_compute_payments_currency', compute_sudo=True, store=False, digits=(16, 4), readonly=True, help='Payments VES')
    company_foreign_currency_id = fields.Many2one('res.currency', string='Moneda extranjera', readonly=True, related='company_id.foreign_currency_id')
    amount_tax_foreign = fields.Monetary(string='Impuestos (Divisa)', readonly=True, currency_field='company_foreign_currency_id')
    amount_total_foreign = fields.Monetary(string='Total (Divisa)', readonly=True, currency_field='company_foreign_currency_id')
    amount_paid_foreign = fields.Monetary(string='Pagado (Divisa)', readonly=True, currency_field='company_foreign_currency_id')
    
    def _compute_show_reason_for_cancellation(self):
        for record in self:
            self.show_reason_for_cancellation = True if (record.order_credit == 'payment_contributions' and record.state != 'cancel' and record.session_id.state != 'closed') else False

    @api.depends('date_order', 'company_id', 'currency_id')
    def _compute_order_credit(self):
        for order in self:
            if (len(order.payment_ids.filtered(lambda x: x.payment_method_id.journal_id == False or len(x.payment_method_id.journal_id) == 0)) > 0):
                if (order.amount_total == 0.0):
                    order.order_credit = 'payment_contributions'
                else:
                    if ('retention_state' in order and (len(self.payment_ids.filtered(lambda x: x.payment_method_id.active_retention)) > 0)):
                        order.order_credit = 'sales_refunds'
                    else:
                        order.order_credit = 'credit_sales'
            else:
                order.order_credit = 'sales_refunds'

    def _compute_payments_currency(self):
        for order in self:
            order.pay_amount_foreign = sum(order.payment_ids.filtered(lambda p: p.amount_foreign != 0).mapped('amount_foreign'))
            pay_amount_foreign_basic = sum(order.payment_ids.filtered(lambda p: p.amount_foreign != 0).mapped('amount'))
            order.pay_amount_cur = sum(order.payment_ids.filtered(lambda p: p.amount_foreign == 0).mapped('amount'))
            if (order.pay_amount_cur < 0):
                if (order.currency_rate_foreign != 0.0):
                    order.pay_amount_foreign = order.pay_amount_foreign + round((order.pay_amount_cur * order.currency_rate_foreign), 2)
                else:
                    order.pay_amount_foreign = order.pay_amount_foreign + round((order.pay_amount_cur * (order.amount_total / order.amount_total_foreign)), 2)
                order.pay_amount_cur = 0
            if (order.pay_amount_foreign < 0):
                order.pay_amount_cur = order.pay_amount_cur + pay_amount_foreign_basic
                order.pay_amount_foreign = 0
                
    @api.depends('date_order', 'company_id', 'currency_id', 'company_id.currency_id')
    def _compute_currency_rate_foreign(self):
        for order in self:
            c_rate = self.env['res.currency.rate'].search([('currency_id', '=', 2), ('company_id', '=', order.company_id.id), ('name', '<=', str(order.date_order)[0:11])], order='name desc', limit=1)
            if (len(c_rate) > 0):
                order.currency_rate_foreign = (1 / c_rate[0].rate)
            else:
                order.currency_rate_foreign = 1

    @api.model_create_multi
    def create(self, vals_list):
        #_logger.warning('create-vals_list: %s', vals_list)
        for vals in vals_list:
            if ('<-pos.order.refunded_order_id' in vals):
                del vals['<-pos.order.refunded_order_id']
        res = super().create(vals_list)
        #_logger.warning('create-res: %s', res)
        return res
        
    '''@api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('order_credit')
        res.append('currency_rate_foreign')
        res.append('amount_tax_foreign')
        res.append('amount_total_foreign')
        res.append('amount_paid_foreign')
        return res
        
    def action_payment_contributions_cancel(self):
        return {
            'name': _('Cancelar aportes de pago'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payment.contributions.cancel',
            'target': 'new',
            'context': { 'default_pos_order_id': self.id }
        }
    
    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        prec_acc = order.pricelist_id.currency_id.decimal_places
        order_bank_statement_lines= self.env['pos.payment'].search([('pos_order_id', '=', order.id)])
        order_bank_statement_lines.unlink()
        for payments in pos_order['statement_ids']:
            order.add_payment(self._payment_fields(order, payments[2]))

        order.amount_paid = sum(order.payment_ids.mapped('amount'))
        if (float(pos_order['amount_total']) < 0):
            if not draft and (float(pos_order['amount_total']) > float(pos_order['amount_paid'])):
                for return_change_id in pos_order['statement_return_change_ids']:
                    pos_order['amount_paid'] = float(pos_order['amount_paid']) + float(return_change_id['amount'])
                    pos_order['amount_return'] = float(pos_order['amount_return']) + float(return_change_id['amount'])
                    order.amount_paid = order.amount_paid + float(return_change_id['amount'])
                    order.amount_return = order.amount_return + float(return_change_id['amount'])
                for return_change_id in pos_order['statement_return_change_ids']:
                    payment_method = pos_session.payment_method_ids.filtered(lambda x: x.id == return_change_id['payment_method_id'])
                    if not payment_method:
                        raise UserError(_("No cash statement found for this session. Unable to record returned."))
                    return_payment_vals = {
                            'name': _('return'),
                            'pos_order_id': order.id,
                            'amount': float(return_change_id['amount']),
                            'amount_foreign': float(return_change_id['amount_foreign']),
                            'payment_date': fields.Datetime.now(),
                            'payment_method_id': payment_method.id,
                            'is_change': True,
                        }
                    order.add_payment(return_payment_vals)
        else:
            if (not draft and not float_is_zero(pos_order['amount_return'], prec_acc)) or (len(pos_order['lines']) == 0 and float(pos_order['amount_total']) == 0):
                for return_change_id in pos_order['statement_return_change_ids']:
                    payment_method = pos_session.payment_method_ids.filtered(lambda x: x.id == return_change_id['payment_method_id'])
                    if not payment_method:
                        raise UserError(_("No cash statement found for this session. Unable to record returned."))
                    return_payment_vals = {
                        'name': _('return'),
                        'pos_order_id': order.id,
                        'amount': - float(return_change_id['amount']),
                        'amount_foreign': - float(return_change_id['amount_foreign']),
                        'payment_date': fields.Datetime.now(),
                        'payment_method_id': payment_method.id,
                        'is_change': True,
                    }
                    order.add_payment(return_payment_vals)

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        res = super()._payment_fields(order, ui_paymentline)
        res['payment_reference'] = ui_paymentline['payment_reference'] if ('payment_reference' in ui_paymentline) else ''
        res['payment_lot'] = ui_paymentline['payment_lot'] if ('payment_lot' in ui_paymentline) else ''
        res['payment_terminal'] = ui_paymentline['payment_terminal'] if ('payment_terminal' in ui_paymentline) else ''
        return res

    @api.model
    def _process_order(self, order, draft, existing_order):
        #_logger.info('_process_order-self: %s', self)
        #_logger.info('_process_order-order: %s', order)
        #_logger.info('_process_order-draft: %s', draft)
        #_logger.info('_process_order-existing_order: %s', existing_order)
        session_id = self.env['pos.session'].search([('id', '=', order['data']['pos_session_id'])], limit=1)
        #_logger.info('_process_order-session_id: %s', session_id)
        #_logger.info('_process_order-cash_rounding: %s', session_id.config_id.cash_rounding)
        if session_id.config_id.cash_rounding:
            if (float(order['data']['amount_total']) != order['data']['amount_paid']):
                amount_diff = order['data']['amount_paid'] - float(order['data']['amount_total'])
                #_logger.info('_process_order-amount_diff: %s', round(amount_diff, 2))
                if (float(order['data']['amount_total']) > order['data']['amount_paid']):
                    order['data']['amount_total'] = float(order['data']['amount_total']) + round(amount_diff, 2)
                else:
                    order['data']['amount_total'] = float(order['data']['amount_total']) + round(amount_diff, 2)
                    #order['data']['amount_paid'] = order['data']['amount_paid'] - round(amount_diff, 2)
                #_logger.info('_process_order-[lines][0]: %s', order['data']['lines'][0])
                #_logger.info('_process_order-[lines][0][2]: %s', order['data']['lines'][0][2])
                #_logger.info('_process_order-[lines][0][2][price_unit]: %s', order['data']['lines'][0][2]['price_unit'])
                #_logger.info('_process_order-tax_id: %s', order['data']['lines'][0][2]['tax_ids'][0][2][0])
                tax_id = self.env['account.tax'].search([('id', '=', order['data']['lines'][0][2]['tax_ids'][0][2][0])], limit=1)
                #_logger.info('_process_order-tax_id: %s', tax_id)

                if (len(tax_id) > 0 and amount_diff != 0.0):
                #if (tax_id.amount > 0):
                    amount_diff = amount_diff / order['data']['lines'][0][2]['qty']
                    amount_diff_base = round((amount_diff / (1 +(tax_id.amount / 100))), 2)
                    _logger.info('_process_order-amount_diff_base: %s', amount_diff_base)
                    amount_diff_tax = round((amount_diff - amount_diff_base), 2)
                    _logger.info('_process_order-amount_diff_tax: %s', amount_diff_tax)
                    order['data']['amount_tax'] = order['data']['amount_tax'] + amount_diff_tax
                    order['data']['lines'][0][2]['price_unit'] = order['data']['lines'][0][2]['price_unit'] + round((amount_diff_base), 2)
                    #_logger.info('_process_order-price_unit: %s', order['data']['lines'][0][2]['price_unit'])
                    order['data']['lines'][0][2]['price_subtotal'] = round((order['data']['lines'][0][2]['qty'] * order['data']['lines'][0][2]['price_unit']), 2) #round((order['data']['lines'][0][2]['price_subtotal'] + amount_diff_base), 2)
                    #_logger.info('_process_order-price_subtotal: %s', order['data']['lines'][0][2]['price_subtotal'])
                    order['data']['lines'][0][2]['price_subtotal_incl'] = order['data']['lines'][0][2]['price_subtotal'] * (1 + (tax_id.amount / 100)) #round((float(order['data']['lines'][0][2]['price_subtotal_incl']) + amount_diff), 2)
                    #_logger.info('_process_order-price_subtotal_incl: %s', order['data']['lines'][0][2]['price_subtotal_incl'])
                    price_subtotal = 0.0
                    price_subtotal_incl_other = 0.0
                    for idx, line in enumerate(order['data']['lines']):
                        #_logger.info('_process_order-idx: %s', idx)
                        #_logger.info('_process_order-line: %s', line)
                        if (idx != 0):
                            price_subtotal_incl_other = price_subtotal_incl_other + float(line[2]['price_subtotal_incl'])
                            price_subtotal = price_subtotal + float(line[2]['price_subtotal'])

                    #_logger.info('_process_order-price_subtotal_incl_other: %s', price_subtotal_incl_other)
                    #_logger.info('_process_order-amount_paid: %s', order['data']['amount_paid'])
                    #_logger.warning('_process_order-data: %s', order['data'])
                    #_logger.warning('_process_order-amount_total: %s', order['data']['amount_total'])
                    #order['data']['amount_total'] = round(order['data']['amount_total'], 2)
                    order['data']['amount_total'] = round((order['data']['lines'][0][2]['price_subtotal_incl'] + price_subtotal_incl_other), 2)
                    amount_paid_diff = round((order['data']['amount_total'] - order['data']['amount_paid']), 2)
                    _logger.warning('_process_order-amount_paid_diff: %s', amount_paid_diff)
                    order['data']['amount_paid'] = round((order['data']['lines'][0][2]['price_subtotal_incl'] + price_subtotal_incl_other), 2)
                    payment_method = self.env['pos.payment.method'].search([('journal_id.type', '=', 'cash')])
                    for idx, statement in enumerate(order['data']['statement_ids']):
                        _logger.warning('_process_order-idx: %s', idx)
                        _logger.warning('_process_order-statement: %s', statement)
                        for pm in payment_method:
                            _logger.warning('_process_order-pm: %s', pm)
                            _logger.warning('_process_order-payment_method_id: %s', order['data']['statement_ids'][idx][2]['payment_method_id'])
                            if (order['data']['statement_ids'][idx][2]['payment_method_id'] == pm.id):
                                _logger.warning('_process_order-amount: %s', order['data']['statement_ids'][idx][2]['amount'])
                                order['data']['statement_ids'][idx][2]['amount'] = order['data']['statement_ids'][idx][2]['amount'] + amount_paid_diff
                                break
                    #_logger.warning('_process_order-amount_total(r): %s', order['data']['amount_total'])
        #_logger.warning('_process_order-data(r): %s', order['data'])
        _logger.warning('_process_order-data(r): %s', order['data'])
        res = super()._process_order(order, draft, existing_order)
        if (len(order['data']['statement_return_change_ids']) > 0):
            ord = self.env['pos.order'].search([('id','=', res)])
            for paym in ord.payment_ids.filtered(lambda x: x.amount > 0 and x.payment_method_id.enable_currencies):
                for stat in order['data']['statement_ids']:
                    if ((stat[2]['payment_method_id'] == paym.payment_method_id.id) and (paym.amount_foreign == stat[2]['amount_foreign']) and 'payment_reference' not in stat[2]):
                        paym.write({ 'amount': stat[2]['amount'] })
                    else:
                        if ('payment_reference' in stat[2] and (paym.payment_reference == stat[2]['payment_reference'])):
                            paym.write({ 'amount': stat[2]['amount'] })
        return res

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        vals['invoice_cash_rounding_id'] = False
        return vals

    def _generate_pos_order_invoice(self):
        #_logger.warning('_generate_pos_order_invoice-self: %s', self)
        if (len(self.lines) == 0):
            return {}

        res = super()._generate_pos_order_invoice()
        #_logger.warning('_generate_pos_order_invoice-res: %s', res)
        #_logger.warning('_generate_pos_order_invoice-res->res_id: %s', res['res_id'])
        if (self.session_id.config_id.cash_rounding):
            move_id = self.env['account.move'].search([('id', '=', res['res_id'])])
            if (len(move_id) > 0):
                #_logger.warning('_generate_pos_order_invoice-res->move_id: %s', move_id)
                if (self.amount_total != move_id.amount_total):
                    move_id._compute_tax_totals_rounding(self.amount_total, self.amount_tax)
                    self._apply_invoice_payments()
        return res

class AccountMove(models.Model):

    _inherit = "account.move"

    def _compute_tax_totals_rounding(self, order_amount_total, order_amount_tax):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        for move in self:
            if move.is_invoice(include_receipts=True):
                move.button_draft()
                base_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
                #_logger.warning('_compute_tax_totals_rounding-base_lines: %s', base_lines)
                base_line_values_list = [line._convert_to_tax_base_line_dict() for line in base_lines]
                #_logger.warning('_compute_tax_totals_rounding-base_line_values_list: %s', base_line_values_list)
                sign = move.direction_sign
                #_logger.warning('_compute_tax_totals_rounding-sign: %s', sign)
                #_logger.warning('_compute_tax_totals_rounding-move.id: %s', move.id)
                if move.id:
                    # The invoice is stored so we can add the early payment discount lines directly to reduce the
                    # tax amount without touching the untaxed amount.
                    base_line_values_list += [
                        {
                            **line._convert_to_tax_base_line_dict(),
                            'handle_price_include': False,
                            'quantity': 1.0,
                            'price_unit': sign * line.amount_foreign,
                        }
                        for line in move.line_ids.filtered(lambda line: line.display_type == 'epd')
                    ]
                    #_logger.warning('_compute_tax_totals_rounding-base_line_values_list(I): %s', base_line_values_list)
                    #for i in range(0, len(base_line_values_list)):
                    base_line_values_list[0]['price_subtotal'] = (base_line_values_list[0]['price_unit'] * base_line_values_list[0]['quantity']) - base_line_values_list[0]['discount']
                    #_logger.warning('_compute_tax_totals_rounding-base_line_values_list(F): %s', base_line_values_list)
                kwargs = {
                    'base_lines': base_line_values_list,
                    'currency': move.currency_id or move.journal_id.currency_id or move.company_id.currency_id,
                }

                if move.id:
                    kwargs['tax_lines'] = [
                        line._convert_to_tax_line_dict()
                        for line in move.line_ids.filtered(lambda line: line.display_type == 'tax')
                    ]
                    #_logger.warning('_compute_tax_totals_rounding-kwargs: %s', kwargs)
                    for i in range(0, len(kwargs['tax_lines'])):
                        kwargs['tax_lines'][0]['tax_amount'] = order_amount_tax
                    #_logger.warning('_compute_tax_totals_rounding-kwargs: %s', kwargs)
                else:
                    # In case the invoice isn't yet stored, the early payment discount lines are not there. Then,
                    # we need to simulate them.
                    epd_aggregated_values = {}
                    for base_line in base_lines:
                        if not base_line.epd_needed:
                            continue
                        for grouping_dict, values in base_line.epd_needed.items():
                            epd_values = epd_aggregated_values.setdefault(grouping_dict, {'price_subtotal': 0.0})
                            epd_values['price_subtotal'] += values['price_subtotal']
                    #_logger.warning('_compute_tax_totals_rounding-epd_values: %s', epd_values)
                    for grouping_dict, values in epd_aggregated_values.items():
                        taxes = None
                        if grouping_dict.get('tax_ids'):
                            taxes = self.env['account.tax'].browse(grouping_dict['tax_ids'][0][2])

                        kwargs['base_lines'].append(self.env['account.tax']._convert_to_tax_base_line_dict(
                            None,
                            partner=move.partner_id,
                            currency=move.currency_id,
                            taxes=taxes,
                            price_unit=values['price_subtotal'],
                            quantity=1.0,
                            account=self.env['account.account'].browse(grouping_dict['account_id']),
                            analytic_distribution=values.get('analytic_distribution'),
                            price_subtotal=values['price_subtotal'],
                            is_refund=move.move_type in ('out_refund', 'in_refund'),
                            handle_price_include=False,
                        ))
                    #_logger.warning('_compute_tax_totals_rounding-kwargs: %s', kwargs)
                move.tax_totals = self.env['account.tax']._prepare_tax_totals(**kwargs)

                if move.invoice_cash_rounding_id:
                    rounding_amount = move.invoice_cash_rounding_id.compute_difference(move.currency_id, move.tax_totals['amount_total'])
                    totals = move.tax_totals
                    totals['display_rounding'] = True
                    if rounding_amount:
                        if move.invoice_cash_rounding_id.strategy == 'add_invoice_line':
                            totals['rounding_amount'] = rounding_amount
                            totals['formatted_rounding_amount'] = formatLang(self.env, totals['rounding_amount'], currency_obj=move.currency_id)
                            totals['amount_total_rounded'] = totals['amount_total'] + rounding_amount
                            totals['formatted_amount_total_rounded'] = formatLang(self.env, totals['amount_total_rounded'], currency_obj=move.currency_id)
                        elif move.invoice_cash_rounding_id.strategy == 'biggest_tax':
                            if totals['subtotals_order']:
                                max_tax_group = max((
                                    tax_group
                                    for tax_groups in totals['groups_by_subtotal'].values()
                                    for tax_group in tax_groups
                                ), key=lambda tax_group: tax_group['tax_group_amount'])
                                max_tax_group['tax_group_amount'] += rounding_amount
                                max_tax_group['formatted_tax_group_amount'] = formatLang(self.env, max_tax_group['tax_group_amount'], currency_obj=move.currency_id)
                                totals['amount_total'] += rounding_amount
                                totals['formatted_amount_total'] = formatLang(self.env, totals['amount_total'], currency_obj=move.currency_id)
                move.action_post()
            else:
                # Non-invoice moves don't support that field (because of multicurrency: all lines of the invoice share the same currency)
                move.tax_totals = None'''