# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from uuid import uuid4
import pytz
from datetime import timedelta
from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_round, float_repr, float_compare
from odoo.exceptions import ValidationError, UserError
from odoo.osv.expression import AND
import base64
import logging
_logger = logging.getLogger(__name__)

class ReportSaleDetails(models.AbstractModel):
    _inherit = "report.point_of_sale.report_saledetails"

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False, **kwargs):
        res = super().get_sale_details(date_start, date_stop, config_ids, session_ids, **kwargs)
        _logger.warning('get_sale_details-res: %s', res)
        return res

    
    '''@api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False, search_type=False, add_orders_details=False):
        #_logger.info('get_sale_details-self: %s', self)
        #_logger.info('get_sale_details-add_orders_details: %s', add_orders_details)
        #_logger.info('get_sale_details-date_start: %s', date_start)
        #_logger.info('get_sale_details-date_stop: %s', date_stop)
        #_logger.info('get_sale_details-config_ids: %s', config_ids)
        #_logger.info('get_sale_details-session_ids: %s', session_ids)
        domain = [('state', 'in', ['paid','invoiced','done'])]
        session = ''
        session_date = ''
        session_rate = 1.0
        sessions = False
        sessionsList = self.env['pos.session'].search([('company_id', '=', self.env.company.id), ('state','=','opened')])
        for sessionItem in sessionsList:
            for order in sessionItem.order_ids:
                if (order.state == 'draft' and ((order.amount_total != 0.0) or (order.amount_total == 0.0 and len(order.lines) == 0))):
                    payment_difference = order.amount_total - sum(order.payment_ids.mapped('amount'))
                    if (abs(payment_difference) < 1):
                        payment_method = sessionItem.config_id.payment_method_ids.filtered(lambda pm: pm.type == 'cash' and (pm.journal_id.currency_id == False or len(pm.journal_id.currency_id) == 0))
                        return_payment_vals = {
                            'name': _('return'),
                            'pos_order_id': order.id,
                            'amount': round(payment_difference, 2),
                            'amount_currency': 0.0,
                            'payment_date': fields.Datetime.now(),
                            'payment_method_id': payment_method[0].id,
                            'is_change': True,
                        }
                        order.add_payment(return_payment_vals)
                        order.write( {'name': order._compute_order_name(), 'state': 'paid' } )
                        if (order.to_invoice == True):
                            order._generate_pos_order_invoice()
        if (session_ids):
            domain = AND([domain, [('session_id', 'in', session_ids)]])
            sessions = self.env['pos.session'].search([('id', 'in', session_ids)])
            if (len(sessions) > 0):
                session = sessions[0].config_id.name + '-' + sessions[0].name
                #_logger.warning('get_sale_details-self: %s', self)
                session_date = str(sessions[0].start_at) + ' - ' + str(sessions[0].stop_at)
                cur = self.env['res.currency.rate'].search([('currency_id', '=', self.env.company.foreign_currency_id.id), ('name', '<=', sessions[0].start_at)], limit=1)
                if (len(cur) > 0):
                    session_rate = round((1 / cur[0].rate), 4)
        else:
            if date_start:
                date_start = fields.Datetime.from_string(date_start)
            else:
                # start by default today 00:00:00
                user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
                today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
                date_start = today.astimezone(pytz.timezone('UTC'))

            if date_stop:
                date_stop = fields.Datetime.from_string(date_stop)
                # avoid a date_stop smaller than date_start
                if (date_stop < date_start):
                    date_stop = date_start + timedelta(days=1, seconds=-1)
            else:
                # stop by default today 23:59:59
                date_stop = date_start + timedelta(days=1, seconds=-1)

            domain = AND([domain,
                [('date_order', '>=', fields.Datetime.to_string(date_start)),
                ('date_order', '<=', fields.Datetime.to_string(date_stop))]
            ])
            cur = self.env['res.currency.rate'].search([('currency_id', '=', self.env.company.foreign_currency_id.id), ('name', '<=', date_start)], limit=1)
            if (len(cur) > 0):
                session_rate = round((1 / cur[0].rate), 4)

            if config_ids:
                domain = AND([domain, [('config_id', 'in', config_ids)]])

        orders = self.env['pos.order'].search(domain)
        user_currency = self.env.company.currency_id
        total = 0.0
        products_sold = {}
        taxes = {}
        taxes_refund = {}
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id._convert(
                    order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
            else:
                total += order.amount_total
            currency = order.session_id.currency_id

            for line in order.lines:
                key = (line.product_id, line.price_unit, line.discount)
                products_sold.setdefault(key, 0.0)
                products_sold[key] += line.qty

                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.sudo().compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        if (order.amount_total > 0.0):
                            taxes.setdefault(tax['id'], {'name': tax['name'], 'tax_amount':0.0, 'base_amount':0.0})
                            taxes[tax['id']]['tax_amount'] += tax['amount']
                            taxes[tax['id']]['base_amount'] += tax['base']
                        else:
                            taxes_refund.setdefault(tax['id'], {'name': tax['name'], 'tax_amount':0.0, 'base_amount':0.0})
                            taxes_refund[tax['id']]['tax_amount'] += tax['amount']
                            taxes_refund[tax['id']]['base_amount'] += tax['base']
                else:
                    if (order.amount_total > 0.0):
                        taxes.setdefault(0, {'name': _('No Taxes'), 'tax_amount':0.0, 'base_amount':0.0})
                        taxes[0]['base_amount'] += line.price_subtotal_incl
                    else:
                        taxes_refund.setdefault(0, {'name': _('No Taxes'), 'tax_amount':0.0, 'base_amount':0.0})
                        taxes_refund[0]['base_amount'] += line.price_subtotal_incl

        payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders.ids)]).ids
        #_logger.info('get_sale_details-sessions: %s', sessions)
        #_logger.info('get_sale_details-sessions-config_id: %s', sessions.config_id)
        #_logger.info('get_sale_details-sessions-config_id.payment_method_ids: %s', sessions.config_id.payment_method_ids)
        #_logger.warning('get_sale_details-payment_ids: %s -> %s', len(payment_ids), payment_ids)
        ppm = self.env['pos.payment.method']
        if payment_ids:
            self.env.cr.execute("""
                SELECT COALESCE(method.name->>%s, method.name->>'en_US') as name, method.id as p_id, journal.type as p_type, method.enable_currencies as enable_currencies, currency.symbol as symbol, currency.position as position, sum(amount) total, sum(ROUND(CASE WHEN (method.enable_currencies = True) THEN (payment.amount_currency) WHEN (po.amount_total = 0.0) THEN (ROUND((payment.amount / po.currency_rate_usd), 4)) ELSE (payment.amount / ROUND((po.amount_total / po.amount_total_foreign), 4)) END, 4)) total_currency """ + (', active_retention as active_retention ' if ('active_retention' in ppm) else ", 'False' as active_retention ") + """
                FROM pos_payment payment INNER JOIN
                     pos_payment_method method ON payment.payment_method_id = method.id LEFT JOIN account_journal journal ON method.journal_id = journal.id LEFT JOIN res_currency currency ON journal.currency_id = currency.id INNER JOIN pos_order po ON payment.pos_order_id = po.id
                WHERE payment.id IN %s AND ((po.order_credit != 'payment_contributions') OR (po.order_credit = 'payment_contributions' AND method.journal_id IS NOT NULL AND payment.amount != 0))
                GROUP BY method.name, method.enable_currencies, method.id, journal.type, currency.symbol, currency.position
            """, (self.env.lang, tuple(payment_ids),))
            payments = self.env.cr.dictfetchall()
            self.env.cr.execute("""
                SELECT COALESCE(method.name->>%s, method.name->>'en_US') as name, method.id as p_id, journal.type as p_type, method.enable_currencies as enable_currencies, currency.symbol as symbol, currency.position as position, sum(amount) total, sum(ROUND(CASE WHEN (method.enable_currencies = True) THEN (payment.amount_currency) WHEN (po.amount_total = 0.0) THEN (ROUND((payment.amount / po.currency_rate_usd), 4)) ELSE (payment.amount / ROUND((po.amount_total / po.amount_total_foreign), 4)) END, 4)) total_currency
                FROM pos_payment payment INNER JOIN
                     pos_payment_method method ON payment.payment_method_id = method.id LEFT JOIN account_journal journal ON method.journal_id = journal.id LEFT JOIN res_currency currency ON journal.currency_id = currency.id INNER JOIN pos_order po ON payment.pos_order_id = po.id
                WHERE payment.id IN %s AND po.order_credit = 'sales_refunds'
                GROUP BY method.name, method.enable_currencies, method.id, journal.type, currency.symbol, currency.position
            """, (self.env.lang, tuple(payment_ids),))
            payments_sales_refunds = self.env.cr.dictfetchall()
            self.env.cr.execute("""
                SELECT COALESCE(method.name->>%s, method.name->>'en_US') as name, method.id as p_id, journal.type as p_type, method.enable_currencies as enable_currencies, currency.symbol as symbol, currency.position as position, sum(amount) total, sum(ROUND(CASE WHEN (method.enable_currencies = True) THEN (payment.amount_currency) WHEN (po.amount_total = 0.0) THEN (ROUND((payment.amount / po.currency_rate_usd), 4)) ELSE (payment.amount / ROUND((po.amount_total / po.amount_total_foreign), 4)) END, 4)) total_currency
                FROM pos_payment payment INNER JOIN
                     pos_payment_method method ON payment.payment_method_id = method.id LEFT JOIN account_journal journal ON method.journal_id = journal.id LEFT JOIN res_currency currency ON journal.currency_id = currency.id INNER JOIN pos_order po ON payment.pos_order_id = po.id
                WHERE payment.id IN %s AND po.order_credit = 'credit_sales'
                GROUP BY method.name, method.enable_currencies, method.id, journal.type, currency.symbol, currency.position
            """, (self.env.lang, tuple(payment_ids),))
            payments_credit_sales = self.env.cr.dictfetchall()
            self.env.cr.execute("""
                SELECT COALESCE(method.name->>%s, method.name->>'en_US') as name, method.id as p_id, journal.type as p_type, method.enable_currencies as enable_currencies, currency.symbol as symbol, currency.position as position, sum(amount) total, sum(ROUND(CASE WHEN (method.enable_currencies = True) THEN (payment.amount_currency) WHEN (po.amount_total = 0.0) THEN (ROUND((payment.amount / po.currency_rate_usd), 4)) ELSE (payment.amount / ROUND((po.amount_total / po.amount_total_foreign), 4)) END, 4)) total_currency
                FROM pos_payment payment INNER JOIN
                     pos_payment_method method ON payment.payment_method_id = method.id LEFT JOIN account_journal journal ON method.journal_id = journal.id LEFT JOIN res_currency currency ON journal.currency_id = currency.id INNER JOIN pos_order po ON payment.pos_order_id = po.id
                WHERE payment.id IN %s AND po.order_credit = 'payment_contributions' AND method.journal_id IS NOT NULL
                GROUP BY method.name, method.enable_currencies, method.id, journal.type, currency.symbol, currency.position
            """, (self.env.lang, tuple(payment_ids),))
            payments_payment_contributions = self.env.cr.dictfetchall()
            self.env.cr.execute("""
                SELECT COALESCE(method.name->>%s, method.name->>'en_US') as name, method.id as p_id, journal.type as p_type, method.enable_currencies as enable_currencies, currency.symbol as symbol, currency.position as position, sum(amount) total, sum(ROUND(CASE WHEN (method.enable_currencies = True) THEN (payment.amount_currency) WHEN (po.amount_total = 0.0) THEN (ROUND((payment.amount / po.currency_rate_usd), 4)) ELSE (payment.amount / ROUND((po.amount_total / po.amount_total_foreign), 4)) END, 4)) total_currency
                FROM pos_payment payment INNER JOIN
                     pos_payment_method method ON payment.payment_method_id = method.id LEFT JOIN account_journal journal ON method.journal_id = journal.id LEFT JOIN res_currency currency ON journal.currency_id = currency.id INNER JOIN pos_order po ON payment.pos_order_id = po.id
                WHERE payment.id IN %s AND po.amount_total < 0.0 AND (po.order_credit = 'sales_refunds' OR po.order_credit = 'credit_sales')
                GROUP BY method.name, method.enable_currencies, method.id, journal.type, currency.symbol, currency.position
            """, (self.env.lang, tuple(payment_ids),))
            payments_refund = self.env.cr.dictfetchall()
            self.env.cr.execute("""
                SELECT COALESCE(method.name->>%s, method.name->>'en_US') as name, method.id as p_id, journal.type as p_type, method.enable_currencies as enable_currencies, currency.symbol as symbol, currency.position as position, sum(amount) total, sum(ROUND(CASE WHEN (method.enable_currencies = True) THEN (payment.amount_currency) WHEN (po.amount_total = 0.0) THEN (ROUND((payment.amount / po.currency_rate_usd), 4)) ELSE (payment.amount / ROUND((po.amount_total / po.amount_total_foreign), 4)) END, 4)) total_currency
                FROM pos_payment payment INNER JOIN
                     pos_payment_method method ON payment.payment_method_id = method.id LEFT JOIN account_journal journal ON method.journal_id = journal.id LEFT JOIN res_currency currency ON journal.currency_id = currency.id INNER JOIN pos_order po ON payment.pos_order_id = po.id
                WHERE payment.id IN %s AND po.amount_total > 0.0 AND po.order_credit = 'sales_refunds'
                GROUP BY method.name, method.enable_currencies, method.id, journal.type, currency.symbol, currency.position
            """, (self.env.lang, tuple(payment_ids),))
            payments_order = self.env.cr.dictfetchall()
        else:
            payments = []
            payments_refund = []
            payments_order = []
            payments_sales_refunds = []
            payments_credit_sales = []
            payments_payment_contributions = []
        #_logger.warning('get_sale_details-payments(o): %s', payments)
        indx = 0
        indx_order = 0
        indx_refund = 0
        indx_sales_refunds = 0
        indx_credit_sales = 0
        indx_payment_contributions = 0
        statement_line_ids = []
        idx_stat_line = 1
        #_logger.info('get_sale_details-payments(I): %s', payments)
        #_logger.warning('get_sale_details-config_ids: %s', config_ids)
        if (session_ids):
            configs = sessions.config_id
        else:
            configs = self.env['pos.config'].search([('id', 'in', config_ids)])
        #_logger.warning('get_sale_details-configs(r): %s', configs)
        for config_id in configs:
            for payment_method_id in config_id.payment_method_ids:
                addMethod = True
                for payment in payments:
                    if (payment_method_id.id == payment['p_id']):
                        #_logger.info('get_sale_details-payment_method_id-(P): %s', payment_method_id)
                        addMethod = False
                for payment in payments_refund:
                    if (payment_method_id.id == payment['p_id']):
                        #_logger.info('get_sale_details-payment_method_id-(P): %s', payment_method_id)
                        addMethod = False
                if (addMethod == True):
                    #_logger.info('get_sale_details-payment_method_id-(A): %s', payment_method_id)
                    payments.append({'name': payment_method_id.name, 'p_id': payment_method_id.id, 'p_type': payment_method_id.journal_id.type, 'enable_currencies': payment_method_id.enable_currencies, 'symbol': (payment_method_id.journal_id.currency_id.symbol if (payment_method_id.journal_id.currency_id != False and len(payment_method_id.journal_id.currency_id) > 0) else self.env.company.currency_id.symbol), 'position': (payment_method_id.journal_id.currency_id.position if (payment_method_id.journal_id.currency_id != False and len(payment_method_id.journal_id.currency_id) > 0) else self.env.company.currency_id.position), 'total': 0.0, 'total_currency': 0.0})
        #_logger.info('get_sale_details-payments(M): %s', payments)
        for payment in payments:
            if (payment['p_type'] == 'cash'):
                if (len(session_ids) == 0):
                    session_ids = self.env['pos.session'].search([('start_at', '>=', date_start), ('stop_at', '<=', date_stop), ('config_id', 'in', configs.ids)]).ids
                statement_ids = self.env['account.bank.statement'].search([('pos_session_id', 'in', session_ids), ('payment_method_id', '=', payment['p_id'])])
                if (len(statement_ids) > 0):
                    for statement_id in statement_ids:
                        if ('opening' in payments[indx]):
                            payments[indx]['opening'] = payments[indx]['opening'] + statement_id[0].opening_balance or 0.0
                            lines = statement_id.line_ids.filtered(lambda x: x.state == 'posted' and x.is_reconciled == False)
                            payments[indx]['in_out'] = payments[indx]['in_out'] + sum(lines.mapped('amount'))
                        else:
                            payments[indx]['opening'] = statement_id[0].opening_balance or 0.0
                            lines = statement_id.line_ids.filtered(lambda x: x.state == 'posted' and x.is_reconciled == False)
                            payments[indx]['in_out'] = sum(lines.mapped('amount'))
                        for line_id in statement_id.line_ids.filtered(lambda x: x.state == 'posted' and x.is_reconciled == False):
                            statement_line_ids.append({ 'position': idx_stat_line, 'date': line_id.date, 'payment_method_name': line_id.pos_payment_method_id.name, 'payment_method_enable_currencies': line_id.pos_payment_method_id.enable_currencies, 'payment_ref': line_id.payment_ref, 'amount': line_id.amount, 'type': 'Entrada' if (line_id.amount > 0.0) else 'Salida', 'currency_position': line_id.pos_payment_method_id.journal_id.currency_id.position if (line_id.pos_payment_method_id.journal_id.currency_id) else self.env.company.currency_id.position, 'currency_symbol': line_id.pos_payment_method_id.journal_id.currency_id.symbol if (line_id.pos_payment_method_id.journal_id.currency_id) else self.env.company.currency_id.symbol })
                            idx_stat_line = idx_stat_line + 1
                else:
                    payments[indx]['opening'] = 0.0
                    payments[indx]['in_out'] = 0.0
                if (payments[indx]['enable_currencies'] == True):
                    payments[indx]['counted'] =  payments[indx]['opening'] + payments[indx]['in_out'] + payments[indx]['total_currency']
                    payments[indx]['counted_currency'] = payments[indx]['counted']
                else:
                    payments[indx]['counted'] = payments[indx]['opening'] + payments[indx]['in_out'] + payments[indx]['total']
                    payments[indx]['counted_currency'] = (payments[indx]['opening'] / session_rate) + (payments[indx]['in_out'] / session_rate) + payments[indx]['total_currency']
            else:
                payments[indx]['opening'] = 0.0
                payments[indx]['in_out'] = 0.0
                if (payments[indx]['enable_currencies'] == True):
                    payments[indx]['counted'] = payments[indx]['total_currency']
                    payments[indx]['counted_currency'] = payments[indx]['counted']
                else:
                    payments[indx]['counted'] = payments[indx]['total']
                    payments[indx]['counted_currency'] = payments[indx]['total_currency']
            if (payment['position'] is None and payment['enable_currencies'] == False):
                payments[indx]['position'] = self.env.company.currency_id.position
                payments[indx]['symbol'] = self.env.company.currency_id.symbol
            if (payment['position'] is None and payment['enable_currencies'] == True):
                payments[indx]['position'] = self.env.company.foreign_currency_id.position
                payments[indx]['symbol'] = self.env.company.foreign_currency_id.symbol
            #_logger.warning('payment: %s', payment)
            if ('active_retention' not in payment or payment['active_retention'] is None or payment['active_retention'] == 'False'):
                payments[indx]['active_retention'] = False
            indx = indx + 1

        for payment in payments_order:
            payments_order[indx_order]['opening'] = 0.0
            payments_order[indx_order]['in_out'] = 0.0
            if (payments_order[indx_order]['total_currency'] is None):
                payments_order[indx_order]['total_currency'] = 0.0
            payments_order[indx_order]['counted'] = (payments_order[indx_order]['total_currency'])
            if (payments_order[indx_order]['counted'] is None):
                payments_order[indx_order]['counted'] = 0.0
            if (payment['position'] is None and payment['enable_currencies'] == False):
                payments_order[indx_order]['position'] = self.env.company.currency_id.position
                payments_order[indx_order]['symbol'] = self.env.company.currency_id.symbol
            if (payment['position'] is None and payment['enable_currencies'] == True):
                payments_order[indx_order]['position'] = self.env.company.foreign_currency_id.position
                payments_order[indx_order]['symbol'] = self.env.company.foreign_currency_id.symbol
            indx_order = indx_order + 1

        for payment in payments_sales_refunds:
            payments_sales_refunds[indx_sales_refunds]['opening'] = 0.0
            payments_sales_refunds[indx_sales_refunds]['in_out'] = 0.0
            if (payments_sales_refunds[indx_sales_refunds]['total_currency'] is None):
                payments_sales_refunds[indx_sales_refunds]['total_currency'] = 0.0
            payments_sales_refunds[indx_sales_refunds]['counted'] = (payments_sales_refunds[indx_sales_refunds]['total_currency'])
            if (payments_sales_refunds[indx_sales_refunds]['counted'] is None):
                payments_sales_refunds[indx_sales_refunds]['counted'] = 0.0
            if (payment['position'] is None and payment['enable_currencies'] == False):
                payments_sales_refunds[indx_sales_refunds]['position'] = self.env.company.currency_id.position
                payments_sales_refunds[indx_sales_refunds]['symbol'] = self.env.company.currency_id.symbol
            if (payment['position'] is None and payment['enable_currencies'] == True):
                payments_sales_refunds[indx_sales_refunds]['position'] = self.env.company.foreign_currency_id.position
                payments_sales_refunds[indx_sales_refunds]['symbol'] = self.env.company.foreign_currency_id.symbol
            indx_sales_refunds = indx_sales_refunds + 1
        #_logger.warning('get_sale_details-payments_credit_sales(r): %s', payments_credit_sales)
        for payment in payments_credit_sales:
            payments_credit_sales[indx_credit_sales]['opening'] = 0.0
            payments_credit_sales[indx_credit_sales]['in_out'] = 0.0
            payments_credit_sales[indx_credit_sales]['p_type_credit'] = True if (payment['p_type'] is None) else False
            if (payments_credit_sales[indx_credit_sales]['total_currency'] is None):
                payments_credit_sales[indx_credit_sales]['total_currency'] = 0.0
            payments_credit_sales[indx_credit_sales]['counted'] = (payments_credit_sales[indx_credit_sales]['total_currency'])
            if (payments_credit_sales[indx_credit_sales]['counted'] is None):
                payments_credit_sales[indx_credit_sales]['counted'] = 0.0
            if (payment['position'] is None and payment['enable_currencies'] == False):
                payments_credit_sales[indx_credit_sales]['position'] = self.env.company.currency_id.position
                payments_credit_sales[indx_credit_sales]['symbol'] = self.env.company.currency_id.symbol
            if (payment['position'] is None and payment['enable_currencies'] == True):
                payments_credit_sales[indx_credit_sales]['position'] = self.env.company.foreign_currency_id.position
                payments_credit_sales[indx_credit_sales]['symbol'] = self.env.company.foreign_currency_id.symbol
            indx_credit_sales = indx_credit_sales + 1

        for payment in payments_payment_contributions:
            payments_payment_contributions[indx_payment_contributions]['opening'] = 0.0
            payments_payment_contributions[indx_payment_contributions]['in_out'] = 0.0
            if (payments_payment_contributions[indx_payment_contributions]['total_currency'] is None):
                payments_payment_contributions[indx_payment_contributions]['total_currency'] = 0.0
            payments_payment_contributions[indx_payment_contributions]['counted'] = (payments_payment_contributions[indx_payment_contributions]['total_currency'])
            if (payments_payment_contributions[indx_payment_contributions]['counted'] is None):
                payments_payment_contributions[indx_payment_contributions]['counted'] = 0.0
            if (payment['position'] is None and payment['enable_currencies'] == False):
                payments_payment_contributions[indx_payment_contributions]['position'] = self.env.company.currency_id.position
                payments_payment_contributions[indx_payment_contributions]['symbol'] = self.env.company.currency_id.symbol
            if (payment['position'] is None and payment['enable_currencies'] == True):
                payments_payment_contributions[indx_payment_contributions]['position'] = self.env.company.foreign_currency_id.position
                payments_payment_contributions[indx_payment_contributions]['symbol'] = self.env.company.foreign_currency_id.symbol
            indx_payment_contributions = indx_payment_contributions + 1

        for payment in payments_refund:
            payments_refund[indx_refund]['opening'] = 0.0
            payments_refund[indx_refund]['in_out'] = 0.0
            if (payments_refund[indx_refund]['total_currency'] is None):
                payments_refund[indx_refund]['total_currency'] = 0.0
            payments_refund[indx_refund]['counted'] = (payments_refund[indx_refund]['total_currency'])
            if (payments_refund[indx_refund]['counted'] is None):
                payments_refund[indx_refund]['counted'] = 0.0
            if (payment['position'] is None and payment['enable_currencies'] == False):
                payments_refund[indx_refund]['position'] = self.env.company.currency_id.position
                payments_refund[indx_refund]['symbol'] = self.env.company.currency_id.symbol
            if (payment['position'] is None and payment['enable_currencies'] == True):
                payments_refund[indx_refund]['position'] = self.env.company.foreign_currency_id.position
                payments_refund[indx_refund]['symbol'] = self.env.company.foreign_currency_id.symbol
            indx_refund = indx_refund + 1
        #_logger.warning('get_sale_details-payments(r): %s', payments)
        foreign_currency = {
            'id': self.env.company.foreign_currency_id.id,
            'name': self.env.company.foreign_currency_id.name,
            'symbol': self.env.company.foreign_currency_id.symbol,
            'position': self.env.company.foreign_currency_id.position,
        }
        orders_sales_refunds = []
        orders_credit_sales = []
        orders_payment_contributions = []
        if (add_orders_details):
            order_idx = 1
            for order in orders.filtered(lambda o: o.amount_total > 0.0 and o.order_credit == 'sales_refunds'):
                order_credit = {'position': order_idx, 'date_order': str(order.date_order), 'name': order.name, 'invoice_name': order.account_move.name, 'partner_name': order.partner_id.name, 'amount_total': order.amount_total, 'amount_total_foreign': order.amount_total_foreign, 'seller_name': order.seller_id.name, 'order_type': ('Factura' if (order.amount_total > 0) else 'Nota de credito') }
                order_idx = order_idx + 1
                orders_sales_refunds.append(order_credit)
            order_idx = 1
            for order in orders.filtered(lambda o: o.amount_total > 0.0 and o.order_credit == 'credit_sales'):
                order_credit = {'position': order_idx, 'date_order': str(order.date_order), 'name': order.name, 'invoice_name': order.account_move.name, 'partner_name': order.partner_id.name, 'amount_total': order.amount_total, 'amount_total_foreign': order.amount_total_foreign, 'payment_credit': round(sum(order.payment_ids.filtered(lambda p: p.payment_method_id.journal_id == False or len(p.payment_method_id.journal_id) == 0).mapped('amount')), 2), 'payment_credit_foreign': round(sum(order.payment_ids.filtered(lambda p: p.payment_method_id.journal_id == False or len(p.payment_method_id.journal_id) == 0).mapped('amount_currency')), 2) }
                order_idx = order_idx + 1
                orders_credit_sales.append(order_credit)
            order_idx = 1
            for order in orders.filtered(lambda o: o.amount_total == 0.0 and o.order_credit == 'payment_contributions'):
                order.partner_id._compute_total_due_foreign_currency()
                order_contributions = {'position': order_idx, 'date_order': str(order.date_order), 'name': order.name, 'partner_name': order.partner_id.name, 'payment_credit': round(sum(order.payment_ids.filtered(lambda p: p.payment_method_id.journal_id).mapped('amount')), 2), 'payment_credit_foreign': round((sum(order.payment_ids.filtered(lambda p: p.payment_method_id.journal_id).mapped('amount')) / session_rate), 2), 'total_due_foreign_currency': order.partner_id.total_due_foreign_currency }
                order_idx = order_idx + 1
                orders_payment_contributions.append(order_contributions)
        #_logger.warning('get_sale_details-foreign_currency(r): %s', foreign_currency)
        #_logger.warning('get_sale_details-payments(r): %s', payments)
        #_logger.warning('get_sale_details-payments_refund(r): %s', payments_refund)
        order_amount_total_foreign_contributions = 0.0
        order_amount_total_acum = round(sum(orders.mapped('amount_total')), 2)
        order_amount_total_acum = order_amount_total_acum + round(sum(orders.payment_ids.filtered(lambda p: p.payment_method_id.journal_id and p.pos_order_id.order_credit == 'payment_contributions').mapped('amount')), 2)
        order_amount_total_acum_foreign = round(sum(orders.mapped('amount_total_foreign')), 2)
        order_amount_total_foreign_contributions = order_amount_total_foreign_contributions + round((sum(orders.payment_ids.filtered(lambda p: p.pos_order_id.amount_total == 0.0 and p.pos_order_id.order_credit == 'payment_contributions' and p.payment_method_id.journal_id and p.payment_method_id.enable_currencies == False).mapped('amount'))/ session_rate), 2)
        order_amount_total_foreign_contributions = order_amount_total_foreign_contributions + round((sum(orders.payment_ids.filtered(lambda p: p.pos_order_id.amount_total == 0.0 and p.pos_order_id.order_credit == 'payment_contributions' and p.payment_method_id.journal_id and p.payment_method_id.enable_currencies == True).mapped('amount_currency'))), 2)
        order_amount_total_acum_foreign = order_amount_total_acum_foreign + order_amount_total_foreign_contributions
        #_logger.warning('get_sale_details-order_amount_total_acum_foreign(r): %s', order_amount_total_acum_foreign)
        #raise UserError('Error')
        return {
            'search_type': search_type,
            'session_rate': session_rate,
            'session': session,
            'session_date': session_date,
            'date_start': date_start,
            'date_stop': date_stop,
            'currency_precision': user_currency.decimal_places,
            'total_paid': user_currency.round(total),
            'payments': payments,
            'payments_sales_refunds': payments_sales_refunds,
            'payments_credit_sales': payments_credit_sales,
            'payments_payment_contributions': payments_payment_contributions,
            'payments_order': payments_order,
            'payments_refund': payments_refund,
            'foreign_currency': foreign_currency,
            'company_name': self.env.company.name,
            'company_currency_symbol': self.env.company.currency_id.symbol,
            'company_currency_position': self.env.company.currency_id.position,
            'taxes': list(taxes.values()),
            'taxes_refund': list(taxes_refund.values()),
            'qty_order': len(orders.filtered(lambda o: o.amount_total > 0.0 and o.order_credit == 'sales_refunds')),
            'order_amount_total': round(sum(orders.filtered(lambda o: o.amount_total > 0.0 and o.order_credit == 'sales_refunds').mapped('amount_total')), 2),
            'order_amount_total_foreign': round(sum(orders.filtered(lambda o: o.amount_total > 0.0 and o.order_credit == 'sales_refunds').mapped('amount_total_foreign')), 2),
            'qty_order_credit': len(orders.filtered(lambda o: o.amount_total > 0.0 and o.order_credit == 'credit_sales')),
            'order_amount_total_credit': round(sum(orders.filtered(lambda o: o.amount_total > 0.0 and o.order_credit == 'credit_sales').mapped('amount_total')), 2),
            'order_amount_total_foreign_credit': round(sum(orders.filtered(lambda o: o.amount_total > 0.0 and o.order_credit == 'credit_sales').mapped('amount_total_foreign')), 2),
            'qty_order_contributions': len(orders.filtered(lambda o: o.amount_total == 0.0 and o.order_credit == 'payment_contributions')),
            'order_amount_total_contributions': round(sum(orders.payment_ids.filtered(lambda p: p.pos_order_id.amount_total == 0.0 and p.pos_order_id.order_credit == 'payment_contributions' and p.payment_method_id.journal_id != False and len(p.payment_method_id.journal_id) > 0).mapped('amount')), 2),
            'order_amount_total_foreign_contributions': order_amount_total_foreign_contributions,
            'qty_order_refund': len(orders.filtered(lambda o: o.amount_total < 0.0 and o.order_credit == 'sales_refunds')),
            'order_amount_total_refund': round(sum(orders.filtered(lambda o: o.amount_total < 0.0 and o.order_credit == 'sales_refunds').mapped('amount_total')), 2),
            'order_amount_total_refund_foreign': round(sum(orders.filtered(lambda o: o.amount_total < 0.0 and o.order_credit == 'sales_refunds').mapped('amount_total_foreign')), 2),
            'qty_order_acum': len(orders),
            'order_amount_total_acum': order_amount_total_acum,
            'order_amount_total_acum_foreign': order_amount_total_acum_foreign,
            'orders_sales_refunds': orders_sales_refunds,
            'orders_credit_sales': orders_credit_sales,
            'orders_payment_contributions': orders_payment_contributions,
            'statement_line_ids': statement_line_ids,
            'products': sorted([{
                'product_id': product.id,
                'product_name': product.name,
                'code': product.default_code,
                'quantity': qty,
                'price_unit': price_unit,
                'discount': discount,
                'uom': product.uom_id.name
            } for (product, price_unit, discount), qty in products_sold.items()], key=lambda l: l['product_name'])
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        # initialize data keys with their value if provided, else None
        if (data.get('search_type') == 'date' and len(docids) == 0):
            data.update({
                'session_ids': data.get('session_ids') or docids,
                'config_ids': data.get('config_ids'),
                'date_start': data.get('date_start'),
                'date_stop': data.get('date_stop'),
                'search_type': data.get('search_type'),
                'add_orders_details': data.get('add_orders_details')
            })
        else:
            data.update({
                'session_ids': data.get('pos_session_ids') or docids,
                'search_type': data.get('search_type'),
                'add_orders_details': data.get('add_orders_details')
            })
        if (data.get('search_type') == 'date'):
            configs = self.env['pos.config'].browse(data['config_ids'])
            data.update(self.get_sale_details(data['date_start'], data['date_stop'], configs.ids, data['session_ids'], data.get('search_type'), data.get('add_orders_details')))
        else:
            data.update(self.get_sale_details(False, False, False, data['session_ids'], data.get('search_type'), data.get('add_orders_details')))
        return data'''