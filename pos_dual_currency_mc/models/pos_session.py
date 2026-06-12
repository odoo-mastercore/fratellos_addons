# -*- coding: utf-8 -*-
import pprint
from odoo import api, _, models, fields
from collections import defaultdict
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from odoo.osv.expression import AND
import logging
_logger = logging.getLogger(__name__)

class PosSession(models.Model):
    _inherit = 'pos.session'

    statement_ids = fields.One2many('account.bank.statement', 'pos_session_id',  string='Efectivos')
    currency_rate = fields.Monetary(string='Tasa de cambio', currency_field='currency_id', compute='_compute_currency_rate', store=False)
        
    @api.model
    def _load_pos_data_models(self, config_id):
        res = super()._load_pos_data_models(config_id)
        res.append('account.bank.statement')
        return res
        
    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('statement_ids')
        res.append('currency_rate')
        return res
        
    def _compute_currency_rate(self):
        for session in self:
            if session:
                accountBankStatement = self.env['account.bank.statement'].sudo().search([('pos_session_id', '=', session.id)],order='name desc')
                for bankStatement in accountBankStatement:
                    #if ((len(bankStatement.journal_id.currency_id) == 0) or (bankStatement.journal_id.currency_id.id == self.env.company.currency_id.id)):
                    if (len(bankStatement.currency_id) > 0 and (bankStatement.currency_id.id != self.env.company.currency_id.id)):
                        cur_rate = self.env['res.currency.rate'].search([('name', '<=', session.start_at), ('company_id', '=', session.company_id.id), ('currency_id', '=', bankStatement.currency_id.id)], limit=1)
                        if (len(cur_rate) > 0):
                            session.currency_rate = round((1 / cur_rate.rate), 2)
                        else:
                             session.currency_rate = 0.0
                if (len(accountBankStatement) == 0):
                    session.currency_rate = 0.0
                if (session.currency_rate == False):
                        session.currency_rate = 0.0
            else:
                session.currency_rate = 0.0

    def action_pos_session_open(self):
        # we only open sessions that haven't already been opened
        for session in self.filtered(lambda session: session.state == 'opening_control'):
            values = {}
            if not session.start_at:
                values['start_at'] = fields.Datetime.now()
            if session.config_id.cash_control and not session.rescue:
                for record in session.payment_method_ids.filtered(lambda p: p.journal_id.type == "cash"):
                    #print('action_pos_session_open-record: ', record)
                    #print('action_pos_session_open-record.journal_id: ', record.journal_id)
                    last_session =  self.env['account.bank.statement'].search([('config_id', '=', session.config_id.id), ('pos_session_id', '!=', session.id), ('payment_method_id', '=', record.id)], limit=1, order ='id desc')
                    #print('action_pos_session_open-last_session: ', last_session)
                    session.cash_register_balance_start = 0 #last_session.cash_register_balance_end_real  # defaults to 0 if lastsession is empty
                    statement_vals = {
                        'name': session.name + ' ' + (record.journal_id.currency_id.name if (len(record.journal_id.currency_id) > 0) else session.company_id.currency_id.name),
                        'date': fields.Datetime.now(),
                        'pos_session_id': session.id,
                        'config_id': session.config_id.id,
                        'balance_start': last_session.balance_end_real if (len(last_session) > 0) else 0,
                        'company_id': record.company_id.id,
                        'currency_id': record.journal_id.currency_id.id if (len(record.journal_id.currency_id) > 0) else session.company_id.currency_id.id,
                        'journal_id': record.journal_id.id,
                        'payment_method_id': record.id
                    }
                    #print('action_pos_session_open-statement_vals: ', statement_vals)
                    statement_id = self.env['account.bank.statement'].sudo().create(statement_vals)
                    statement_id.write({'journal_id': record.journal_id.id, 'company_id': record.company_id.id, 'opening_balance': statement_id.balance_end})
                    ##_logger.info('action_pos_session_open-statement_id: %s', statement_id)
            session.write(values)
        return True

    def get_bank_statement(self):
        statement_ids = self.env['account.bank.statement'].search([('pos_session_id', '=', self.id)])
        statement_id = []
        for statement in statement_ids:
            statement_id.append({
                'id': statement.id,
                'name':statement.name,
                'date':statement.date,
                'balance_start':statement.balance_start,
                'balance_end':statement.balance_end,
                'balance_end_real':statement.balance_end_real,
                'company_id':statement.company_id.id,
                'currency_id':statement.currency_id.id,
                'journal_id':statement.journal_id.id,
                'payment_method_id':statement.payment_method_id.id,
                'payment_method_enable_amount_opening':statement.payment_method_id.enable_amount_opening,
                'payment_method_amount_opening':statement.payment_method_id.amount_opening
            })
        return statement_id

    def _post_statement_difference_multicash(self, amount, statement_id, pos_payment_method_id):
        if amount:
            if self.config_id.cash_control:
                st_line_vals = {
                    'journal_id': statement_id.journal_id.id,
                    'amount': amount,
                    'date': self.statement_line_ids.sorted()[-1:].date or fields.Date.context_today(self),
                    'pos_session_id': self.id,
                    'pos_payment_method_id': pos_payment_method_id,
                    'statement_id': statement_id.id,
                }
            if amount < 0.0:
                if not statement_id.journal_id.loss_account_id:
                    raise UserError(
                        _('Please go on the %s journal and define a Loss Account. This account will be used to record cash difference.',
                          statement_id.journal_id.name))

                st_line_vals['payment_ref'] = _("Cash difference observed during the counting (Loss)")
                st_line_vals['counterpart_account_id'] = statement_id.journal_id.loss_account_id.id
            else:
                # self.cash_register_difference  > 0.0
                if not statement_id.journal_id.profit_account_id:
                    raise UserError(
                        _('Please go on the %s journal and define a Profit Account. This account will be used to record cash difference.',
                          statement_id.journal_id.name))

                st_line_vals['payment_ref'] = _("Cash difference observed during the counting (Profit)")
                st_line_vals['counterpart_account_id'] = statement_id.journal_id.profit_account_id.id
            self.env['account.bank.statement.line'].create(st_line_vals)

    def _create_account_move(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        account_move = self.env['account.move'].create({
            'journal_id': self.config_id.journal_id.id,
            'date': fields.Date.context_today(self),
            'ref': self.name,
        })
        self.write({'move_id': account_move.id})

        data = {'bank_payment_method_diffs': bank_payment_method_diffs or {}}
        data = self._accumulate_amounts(data)
        data = self._create_non_reconciliable_move_lines(data)
        data = self._create_bank_payment_moves(data)
        data = self._create_pay_later_receivable_lines(data)
        data = self._create_cash_statement_lines_and_cash_move_lines(data)
        data = self._create_invoice_receivable_lines(data)
        data = self._create_stock_output_lines(data)
        if balancing_account and amount_to_balance:
            data = self._create_balancing_line(data, balancing_account, amount_to_balance)
        return data
    
    def _update_amounts(self, old_amounts, amounts_to_add, date, round=True, force_company_currency=False):
        res = super()._update_amounts(old_amounts, amounts_to_add, date, round, force_company_currency)
        if ('amount_foreign' in amounts_to_add):
            res['amount_foreign'] += amounts_to_add.get('amount_foreign')
        return res
    
    def _accumulate_amounts(self, data):
        # Accumulate the amounts for each accounting lines group
        # Each dict maps `key` -> `amounts`, where `key` is the group key.
        # E.g. `combine_receivables_bank` is derived from pos.payment records
        # in the self.order_ids with group key of the `payment_method_id`
        # field of the pos.payment record.
        AccountTax = self.env['account.tax']
        amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'amount_foreign': 0.0}
        tax_amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'base_amount': 0.0, 'base_amount_converted': 0.0}
        split_receivables_bank = defaultdict(amounts)
        split_receivables_cash = defaultdict(amounts)
        split_receivables_pay_later = defaultdict(amounts)
        combine_receivables_bank = defaultdict(amounts)
        combine_receivables_cash = defaultdict(amounts)
        combine_receivables_pay_later = defaultdict(amounts)
        combine_invoice_receivables = defaultdict(amounts)
        split_invoice_receivables = defaultdict(amounts)
        sales = defaultdict(amounts)
        taxes = defaultdict(tax_amounts)
        stock_expense = defaultdict(amounts)
        stock_return = defaultdict(amounts)
        stock_output = defaultdict(amounts)
        rounding_difference = {'amount': 0.0, 'amount_converted': 0.0}
        # Track the receivable lines of the order's invoice payment moves for reconciliation
        # These receivable lines are reconciled to the corresponding invoice receivable lines
        # of this session's move_id.
        combine_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        split_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        pos_receivable_account = self.company_id.account_default_pos_receivable_account_id
        currency_rounding = self.currency_id.rounding
        closed_orders = self._get_closed_orders()
        for order in closed_orders:
            order_is_invoiced = order.is_invoiced
            for payment in order.payment_ids:
                amount = payment.amount
                amount_foreign = payment.amount_foreign
                if float_is_zero(amount, precision_rounding=currency_rounding):
                    continue
                date = payment.payment_date
                payment_method = payment.payment_method_id
                is_split_payment = payment.payment_method_id.split_transactions
                payment_type = payment_method.type

                # If not pay_later, we create the receivable vals for both invoiced and uninvoiced orders.
                #   Separate the split and aggregated payments.
                # Moreover, if the order is invoiced, we create the pos receivable vals that will balance the
                # pos receivable lines from the invoice payments.
                if payment_type != 'pay_later':
                    if is_split_payment and payment_type == 'cash':
                        split_receivables_cash[payment] = self._update_amounts(split_receivables_cash[payment], {'amount': amount, 'amount_foreign': amount_foreign}, date)
                    elif not is_split_payment and payment_type == 'cash':
                        combine_receivables_cash[payment_method] = self._update_amounts(combine_receivables_cash[payment_method], {'amount': amount, 'amount_foreign': amount_foreign}, date)
                    elif is_split_payment and payment_type == 'bank':
                        split_receivables_bank[payment] = self._update_amounts(split_receivables_bank[payment], {'amount': amount, 'amount_foreign': amount_foreign}, date)
                    elif not is_split_payment and payment_type == 'bank':
                        combine_receivables_bank[payment_method] = self._update_amounts(combine_receivables_bank[payment_method], {'amount': amount, 'amount_foreign': amount_foreign}, date)

                    # Create the vals to create the pos receivables that will balance the pos receivables from invoice payment moves.
                    if order_is_invoiced:
                        if is_split_payment:
                            split_inv_payment_receivable_lines[payment] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            split_invoice_receivables[payment] = self._update_amounts(split_invoice_receivables[payment], {'amount': payment.amount, 'amount_foreign': amount_foreign}, order.date_order)
                        else:
                            combine_inv_payment_receivable_lines[payment_method] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            combine_invoice_receivables[payment_method] = self._update_amounts(combine_invoice_receivables[payment_method], {'amount': payment.amount, 'amount_foreign': amount_foreign}, order.date_order)

                # If pay_later, we create the receivable lines.
                #   if split, with partner
                #   Otherwise, it's aggregated (combined)
                # But only do if order is *not* invoiced because no account move is created for pay later invoice payments.
                if payment_type == 'pay_later' and not order_is_invoiced:
                    if is_split_payment:
                        split_receivables_pay_later[payment] = self._update_amounts(split_receivables_pay_later[payment], {'amount': amount, 'amount_foreign': amount_foreign}, date)
                    elif not is_split_payment:
                        combine_receivables_pay_later[payment_method] = self._update_amounts(combine_receivables_pay_later[payment_method], {'amount': amount, 'amount_foreign': amount_foreign}, date)

            if not order_is_invoiced:
                base_lines = order.with_context(linked_to_pos=True)._prepare_tax_base_line_values()
                AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
                AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
                AccountTax._add_accounting_data_in_base_lines_tax_details(base_lines, order.company_id, include_caba_tags=True)
                tax_results = AccountTax._prepare_tax_lines(base_lines, order.company_id)
                total_amount_currency = 0.0
                for base_line, to_update in tax_results['base_lines_to_update']:
                    # Combine sales/refund lines
                    sale_key = (
                        # account
                        base_line['account_id'].id,
                        # sign
                        -1 if base_line['is_refund'] else 1,
                        # for taxes
                        tuple(base_line['record'].tax_ids_after_fiscal_position.flatten_taxes_hierarchy().ids),
                        tuple(base_line['tax_tag_ids'].ids),
                        base_line['product_id'].id if self.config_id.is_closing_entry_by_product else False,
                    )
                    total_amount_currency += to_update['amount_currency']
                    sales[sale_key] = self._update_amounts(
                        sales[sale_key],
                        {
                            'amount': to_update['amount_currency'],
                            'amount_converted': to_update['balance'],
                        },
                        order.date_order,
                    )
                    if self.config_id.is_closing_entry_by_product:
                        sales[sale_key] = self._update_quantities(sales[sale_key], base_line['quantity'])

                # Combine tax lines
                for tax_line in tax_results['tax_lines_to_add']:
                    tax_key = (
                        tax_line['account_id'],
                        tax_line['tax_repartition_line_id'],
                        tuple(tax_line['tax_tag_ids'][0][2]),
                    )
                    total_amount_currency += tax_line['amount_currency']
                    taxes[tax_key] = self._update_amounts(
                        taxes[tax_key],
                        {
                            'amount': tax_line['amount_currency'],
                            'amount_converted': tax_line['balance'],
                            'base_amount': tax_line['tax_base_amount']
                        },
                        order.date_order,
                    )

                if self.config_id.cash_rounding:
                    diff = order.amount_paid + total_amount_currency
                    rounding_difference = self._update_amounts(rounding_difference, {'amount': diff}, order.date_order)

                # Increasing current partner's customer_rank
                partners = (order.partner_id | order.partner_id.commercial_partner_id)
                partners._increase_rank('customer_rank')

        if self.company_id.anglo_saxon_accounting:
            all_picking_ids = self.order_ids.filtered(lambda p: not p.is_invoiced and not p.shipping_date).picking_ids.ids + self.picking_ids.filtered(lambda p: not p.pos_order_id).ids
            if all_picking_ids:
                # Combine stock lines
                stock_move_sudo = self.env['stock.move'].sudo()
                stock_moves = stock_move_sudo.search([
                    ('picking_id', 'in', all_picking_ids),
                    ('company_id.anglo_saxon_accounting', '=', True),
                    ('product_id.categ_id.property_valuation', '=', 'real_time'),
                    ('product_id.is_storable', '=', True),
                ])
                for stock_moves_split in self.env.cr.split_for_in_conditions(stock_moves.ids):
                    stock_moves_batch = stock_move_sudo.browse(stock_moves_split)
                    candidates = stock_moves_batch\
                        .filtered(lambda m: not bool(m.origin_returned_move_id and sum(m.stock_valuation_layer_ids.mapped('quantity')) >= 0))\
                        .mapped('stock_valuation_layer_ids')
                    for move in stock_moves_batch.with_context(candidates_prefetch_ids=candidates._prefetch_ids):
                        exp_key = move.product_id._get_product_accounts()['expense']
                        out_key = move.product_id.categ_id.property_stock_account_output_categ_id
                        signed_product_qty = move.product_qty
                        if move._is_in():
                            signed_product_qty *= -1
                        amount = signed_product_qty * move.product_id._compute_average_price(0, move.quantity, move)
                        stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                        if move._is_in():
                            stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                        else:
                            stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
        MoveLine = self.env['account.move.line'].with_context(check_move_validity=False, skip_invoice_sync=True)

        data.update({
            'taxes':                               taxes,
            'sales':                               sales,
            'stock_expense':                       stock_expense,
            'split_receivables_bank':              split_receivables_bank,
            'combine_receivables_bank':            combine_receivables_bank,
            'split_receivables_cash':              split_receivables_cash,
            'combine_receivables_cash':            combine_receivables_cash,
            'combine_invoice_receivables':         combine_invoice_receivables,
            'split_receivables_pay_later':         split_receivables_pay_later,
            'combine_receivables_pay_later':       combine_receivables_pay_later,
            'stock_return':                        stock_return,
            'stock_output':                        stock_output,
            'combine_inv_payment_receivable_lines': combine_inv_payment_receivable_lines,
            'rounding_difference':                 rounding_difference,
            'MoveLine':                            MoveLine,
            'split_invoice_receivables': split_invoice_receivables,
            'split_inv_payment_receivable_lines': split_inv_payment_receivable_lines,
        })
        return data
    
    def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        bank_payment_method_diffs = bank_payment_method_diffs or {}
        self.ensure_one()
        data = {}
        sudo = self.env.user.has_group('point_of_sale.group_pos_user')
        if self.get_session_orders().filtered(lambda o: o.state != 'cancel') or self.sudo().statement_line_ids:
            self.cash_real_transaction = sum(self.sudo().statement_line_ids.mapped('amount'))
            if self.state == 'closed':
                raise UserError(_('This session is already closed.'))
            self._check_if_no_draft_orders()
            self._check_invoices_are_posted()
            cash_difference_before_statements = self.cash_register_difference
            if self.update_stock_at_closing:
                self._create_picking_at_end_of_session()
                self.order_ids.filtered(lambda o: not o.is_total_cost_computed)._compute_total_cost_at_session_closing(self.picking_ids.move_ids)
            try:
                with self.env.cr.savepoint():
                    #raise UserError('_validate_session-Error1!')
                    data = self.with_company(self.company_id).with_context(check_move_validity=False, skip_invoice_sync=True)._create_account_move(balancing_account, amount_to_balance, bank_payment_method_diffs)
            except AccessError as e:
                if sudo:
                    #raise UserError('_validate_session-Error2!')
                    data = self.sudo().with_company(self.company_id).with_context(check_move_validity=False, skip_invoice_sync=True)._create_account_move(balancing_account, amount_to_balance, bank_payment_method_diffs)
                else:
                    raise e

            balance = sum(self.move_id.line_ids.mapped('balance'))
            try:
                with self.move_id._check_balanced({'records': self.move_id.sudo()}):
                    pass
            except UserError:
                # Creating the account move is just part of a big database transaction
                # when closing a session. There are other database changes that will happen
                # before attempting to create the account move, such as, creating the picking
                # records.
                # We don't, however, want them to be committed when the account move creation
                # failed; therefore, we need to roll back this transaction before showing the
                # close session wizard.
                self.env.cr.rollback()
                return self._close_session_action(balance)
            #raise UserError('_validate_session-cash_difference_before_statements!')
            self.sudo()._post_statement_difference(cash_difference_before_statements)
            if self.move_id.line_ids:
                self.move_id.sudo().with_company(self.company_id)._post()
                #We need to write the price_subtotal and price_total here because if we do it earlier the compute functions will overwrite it here /account/models/account_move_line.py _compute_totals
                for dummy, amount_data in data['sales'].items():
                    self.env['account.move.line'].browse(amount_data['move_line_id']).sudo().with_company(self.company_id).write({
                        'price_subtotal': abs(amount_data['amount_converted']),
                        'price_total': abs(amount_data['amount_converted']) + abs((amount_data['tax_amount'] if ('tax_amount' in amount_data) else 0.0)),
                    })
                # Set the uninvoiced orders' state to 'done'
                self.env['pos.order'].search([('session_id', '=', self.id), ('state', '=', 'paid')]).write({'state': 'done'})
            else:
                self.move_id.sudo().unlink()
            self.sudo().with_company(self.company_id)._reconcile_account_move_lines(data)
        else:
            #_logger.warning('_validate_session-cash_register_difference: %s', self.cash_register_difference)
            #raise UserError('_validate_session-cash_difference_before_statements! 2')
            self.sudo()._post_statement_difference(self.cash_register_difference)
        #raise UserError('_validate_session-Error3!')
        self.write({'state': 'closed'})
        return True

    def validate_orders_pending_for_closing(self):
        sessions = self.env['pos.session'].search([('state', '=', 'opened')])
        for ps in sessions:
            for order in ps.order_ids.filtered(lambda o: o.state != 'cancel'):
                if (order.state == 'draft' and order.amount_total != 0.0):
                    payment_difference = order.amount_total - sum(order.payment_ids.mapped('amount'))
                    if (abs(payment_difference) < 1):
                        payment_method = self.config_id.payment_method_ids.filtered(lambda pm: pm.type == 'cash' and (pm.journal_id.currency_id == False or len(pm.journal_id.currency_id) == 0))
                        return_payment_vals = {
                            'name': _('return'),
                            'pos_order_id': order.id,
                            'amount': round(payment_difference, 2),
                            'amount_foreign': 0.0,
                            'payment_date': fields.Datetime.now(),
                            'payment_method_id': payment_method.id,
                            'is_change': True,
                        }
                        order.add_payment(return_payment_vals)
                        order.write( {'name': order._compute_order_name() } )
                        if (order.to_invoice == True or order.config_id.forced_button_invoice == True):
                            order._generate_pos_order_invoice()

    def _create_combine_account_payment(self, payment_method, amounts, diff_amount):
        outstanding_account = payment_method.outstanding_account_id
        destination_account = self._get_receivable_account(payment_method)
        '''if float_compare(amounts['amount'], 0, precision_rounding=self.currency_id.rounding) < 0:
            outstanding_account, destination_account = destination_account, outstanding_account'''
        account_payment = self.env['account.payment'].with_context(pos_payment=True).create({
            'amount': abs(amounts['amount']) + diff_amount,
            'journal_id': payment_method.journal_id.id,
            'force_outstanding_account_id': outstanding_account.id,
            'destination_account_id':  destination_account.id,
            'memo': _('Combine %(payment_method)s POS payments from %(session)s', payment_method=payment_method.name, session=self.name),
            'pos_payment_method_id': payment_method.id,
            'pos_session_id': self.id,
            'company_id': self.company_id.id,
            'payment_lot': self.env['pos.payment'].search([('payment_method_id','=', payment_method.id),('pos_order_id','in', [rec.id for rec in self.order_ids])])[0].payment_lot,
            'payment_terminal': self.env['pos.payment'].search([('payment_method_id','=', payment_method.id),('pos_order_id','in', [rec.id for rec in self.order_ids])])[0].payment_terminal,
            'payment_reference': self.env['pos.payment'].search([('payment_method_id','=', payment_method.id),('pos_order_id','in', [rec.id for rec in self.order_ids])])[0].payment_reference
        })

        accounting_installed = self.env['account.move']._get_invoice_in_payment_state() == 'in_payment'
        if not account_payment.outstanding_account_id and accounting_installed:
            account_payment.outstanding_account_id = account_payment._get_outstanding_account(account_payment.payment_type)

        if float_compare(amounts['amount'], 0, precision_rounding=self.currency_id.rounding) < 0:
            # revert the accounts because account.payment doesn't accept negative amount.
            account_payment.write({
                'outstanding_account_id': account_payment.destination_account_id,
                'destination_account_id': account_payment.outstanding_account_id,
                'payment_type': 'outbound',
            })

        account_payment.action_post()

        diff_amount_compare_to_zero = self.currency_id.compare_amounts(diff_amount, 0)
        if diff_amount_compare_to_zero != 0:
            self._apply_diff_on_account_payment_move(account_payment, payment_method, diff_amount)

        return account_payment.move_id.line_ids.filtered(lambda line: line.account_id == self._get_receivable_account(payment_method))

        '''diff_amount_compare_to_zero = self.currency_id.compare_amounts(diff_amount, 0)
        if diff_amount_compare_to_zero != 0:
            self._apply_diff_on_account_payment_move(account_payment, payment_method, diff_amount)

        account_payment.action_post()
        return account_payment.move_id.line_ids.filtered(lambda line: line.account_id == account_payment.destination_account_id)'''
        
    def set_opening_control_payment_method(self, paymentMethodCashId, cashbox_value, notes):
        if self.state != 'opening_control':
            return
        self.state = 'opened'
        self.start_at = fields.Datetime.now()
        if not self.rescue:
            self.name = self.env['ir.sequence'].with_context(company_id=self.config_id.company_id.id).next_by_code('pos.session')
        cash_register_balance_start = 0.0
        for payMethodCash in paymentMethodCashId:
            #_logger.warning('payMethodCash: %s', payMethodCash)
            #_logger.warning('cashbox_value: %s', cashbox_value)
            #_logger.warning('statement_ids: %s', self.statement_ids)
            stat_index = self.statement_ids.filtered(lambda statement_id: statement_id.pos_session_id.id == self.id and statement_id.payment_method_id.id == payMethodCash['id'])
            #_logger.warning('stat_index: %s', stat_index)
            self.opening_notes = notes
            difference = round((float(cashbox_value[str(payMethodCash['id'])].replace('.', '').replace(',', '.')) - stat_index.balance_start), 2) #cashbox_value - self.cash_register_balance_start
            vals = {'opening_balance': float(cashbox_value[str(payMethodCash['id'])].replace('.', '').replace(',', '.')), 'balance_end_real': 0.0 }
            if (stat_index.payment_method_id.enable_currencies):
                vals['opening_balance_default'] = round(vals['opening_balance'] / stat_index.payment_method_id.currency_rate, 2)
            else:
                vals['opening_balance_default'] = vals['opening_balance']
            #_logger.warning('payMethodCash-vals: %s', vals)
            stat_index.write(vals)
            self._post_cash_details_message('Opening cash', self.cash_register_balance_start, difference, notes)
            cash_register_balance_start = cash_register_balance_start + vals['opening_balance_default']
            #_logger.warning('payMethodCash-cash_register_balance_start: %s', cash_register_balance_start)
        self.cash_register_balance_start = cash_register_balance_start

    def get_closing_control_data(self):
        if not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessError(_("You don't have the access rights to get the point of sale closing control data."))
        self.ensure_one()
        for order in self.order_ids:
            if (order.state == 'draft' and ((order.amount_total != 0.0) or (order.amount_total == 0.0 and len(order.lines) == 0))):
                payment_difference = order.amount_total - sum(order.payment_ids.mapped('amount'))
                if (abs(payment_difference) < 1):
                    payment_method = self.config_id.payment_method_ids.filtered(lambda pm: pm.type == 'cash' and (pm.journal_id.currency_id == False or len(pm.journal_id.currency_id) == 0))
                    return_payment_vals = {
                        'name': _('return'),
                        'pos_order_id': order.id,
                        'amount': round(payment_difference, 2),
                        'amount_foreign': 0.0,
                        'payment_date': fields.Datetime.now(),
                        'payment_method_id': payment_method[0].id,
                        'is_change': True,
                    }
                    order.add_payment(return_payment_vals)
                    order.write( {'name': order._compute_order_name(), 'state': 'paid' } )
                    if (order.to_invoice == True):
                        order._generate_pos_order_invoice()
        orders = self._get_closed_orders()
        payments = orders.payment_ids.filtered(lambda p: p.payment_method_id.type != "pay_later")
        pay_later_payments = orders.payment_ids - payments
        pay_later_payments = pay_later_payments.filtered(lambda p: (p.pos_order_id.order_credit != 'payment_contributions') or (p.pos_order_id.order_credit == 'payment_contributions' and p.payment_method_id.journal_id and p.amount > 0))
        default_cash_payment_method_id = None
        balance_start_pay = {}

        for payment_method_id in self.payment_method_ids:
            if (payment_method_id.type == 'cash' and (len(payment_method_id.journal_id.currency_id) == 0 or payment_method_id.journal_id.currency_id.id == self.env.company.currency_id.id)):
                default_cash_payment_method_id = payment_method_id
                statement_id = self.env['account.bank.statement'].sudo().search([('pos_session_id', '=', self.id), ('journal_id', '=', payment_method_id.journal_id.id)],order='name desc', limit=1)
                balance_start_pay[payment_method_id.id] = (statement_id.opening_balance if (len(statement_id) > 0) else 0.0)
            elif (payment_method_id.type == 'cash'):
                statement_id = self.env['account.bank.statement'].sudo().search([('pos_session_id', '=', self.id), ('journal_id', '=', payment_method_id.journal_id.id)],order='name desc', limit=1)
                balance_start_pay[payment_method_id.id] = (statement_id.opening_balance if (len(statement_id) > 0) else 0.0)

        total_default_cash_payment_amount = sum(payments.filtered(lambda p: p.payment_method_id == default_cash_payment_method_id).mapped('amount')) if default_cash_payment_method_id else 0
        total_default_cash_payment_amount_pay = sum(payments.filtered(lambda p: (p.payment_method_id == default_cash_payment_method_id and p.amount > 0)).mapped('amount')) if default_cash_payment_method_id else 0
        total_default_cash_payment_amount_change = sum(payments.filtered(lambda p: (p.payment_method_id == default_cash_payment_method_id and p.amount < 0)).mapped('amount')) if default_cash_payment_method_id else 0
        other_payment_method_ids = self.payment_method_ids - default_cash_payment_method_id if default_cash_payment_method_id else self.payment_method_ids
        cash_in_count = 0
        cash_out_count = 0
        cash_in_out_list = {}
        cash_in_out = {}
        #accountBankStatement = self.env['account.bank.statement'].sudo().search([('pos_session_id', '=', self.id)],order='name desc')
        #_logger.warning('statement_ids: %s', self.statement_ids)
        if self.statement_ids: #accountBankStatement:
            #print('cash_register_id: ', cash_register_id)
            #print('cash_register_id.line_ids: ', cash_register_id.line_ids)
            for cash_move in self.sudo().statement_line_ids.sorted('create_date'):
                if cash_move.amount > 0:
                    cash_in_count += 1
                    name = f'Cash in {cash_in_count}'
                else:
                    cash_out_count += 1
                    name = f'Cash out {cash_out_count}'
                if cash_move.pos_payment_method_id:
                    cash_in_out[cash_move.pos_payment_method_id.id] = (cash_in_out[cash_move.pos_payment_method_id.id] if (cash_move.pos_payment_method_id.id in cash_in_out) else 0) + cash_move.amount
                    if (cash_move.pos_payment_method_id.id not in cash_in_out_list):
                        cash_in_out_list[cash_move.pos_payment_method_id.id] = []
                else:
                    cash_in_out[default_cash_payment_method_id.id] = (cash_in_out[default_cash_payment_method_id.id] if (default_cash_payment_method_id.id in cash_in_out) else 0) + cash_move.amount
                    if (default_cash_payment_method_id.id not in cash_in_out_list):
                        cash_in_out_list[default_cash_payment_method_id.id] = []
                if (len(cash_move.pos_payment_method_id) > 0):
                    if (len(cash_move.pos_payment_method_id.journal_id.currency_id) > 0):
                        cash_in_out_list[cash_move.pos_payment_method_id.id].append({
                            'index': cash_move.id,
                            'name': cash_move.payment_ref if cash_move.payment_ref else name,
                            'amount': cash_move.amount,
                            'pos_payment_method_id': cash_move.pos_payment_method_id.id,
                            'currency_format': {
                                'id': cash_move.pos_payment_method_id.journal_id.currency_id.id,
                                'symbol': cash_move.pos_payment_method_id.journal_id.currency_id.symbol,
                                'position': cash_move.pos_payment_method_id.journal_id.currency_id.position,
                                'rounding': cash_move.pos_payment_method_id.journal_id.currency_id.rounding,
                                'decimals': cash_move.pos_payment_method_id.journal_id.currency_id.decimal_places
                            }
                        })
                    else:
                        cash_in_out_list[cash_move.pos_payment_method_id.id].append({
                            'index': cash_move.id,
                            'name': cash_move.payment_ref if cash_move.payment_ref else name,
                            'amount': cash_move.amount,
                            'pos_payment_method_id': cash_move.pos_payment_method_id.id,
                            'currency_format': {
                                'id': self.env.company.currency_id.id,
                                'symbol': self.env.company.currency_id.symbol,
                                'position': self.env.company.currency_id.position,
                                'rounding': self.env.company.currency_id.rounding,
                                'decimals': self.env.company.currency_id.decimal_places
                            }
                        })
                else:
                    cash_in_out_list[default_cash_payment_method_id.id].append({
                        'index': cash_move.id,
                        'name': cash_move.payment_ref if cash_move.payment_ref else name,
                        'amount': cash_move.amount,
                        'pos_payment_method_id': default_cash_payment_method_id.id,
                        'currency_format': {
                            'id': self.env.company.currency_id.id,
                            'symbol': self.env.company.currency_id.symbol,
                            'position': self.env.company.currency_id.position,
                            'rounding': self.env.company.currency_id.rounding,
                            'decimals': self.env.company.currency_id.decimal_places
                        }
                    })
        #print('self.config_id: ', self.config_id)
        #print('self.config_id.show_currency: ', self.config_id.show_currency)
        #_logger.warning('cash_in_out_list: %s', cash_in_out_list)
        if (self.config_id.show_currency):
            if (self.config_id.show_currency.id != self.env.company.currency_id.id):
                rate = self.env['res.currency.rate'].sudo().search([('currency_id', '=', self.config_id.show_currency.id)],order='name desc', limit=1)[0].rate
            else:
                pricelist = self.env['product.pricelist'].sudo().search([('currency_id', '!=', self.config_id.show_currency.id)])
                if (len(pricelist) > 0):
                    rate = self.env['res.currency.rate'].sudo().search([('currency_id', '=', pricelist.currency_id.id)],order='name desc', limit=1)[0].rate
                else:
                    rate = 1
        else:
            rate = 1

        amount_usd = 0
        payments_amount_foreign = 0
        pay_later_amount_foreign = 0
        amount_usd = round((sum(orders.mapped('amount_total')) * rate), 2)
        payments_amount_foreign = round((sum(payments.mapped('amount')) * rate), 2)
        pay_later_amount_foreign = round((sum(pay_later_payments.mapped('amount')) * rate), 2)

        rate_other_pay = {}
        for o_payment_method in other_payment_method_ids:
            if (o_payment_method.journal_id.currency_id):
                if (o_payment_method.journal_id.currency_id.id == self.config_id.show_currency.id):
                    rate_other_pay[o_payment_method.id] = rate
                else:
                    rate_other_pay[o_payment_method.id] = self.env['res.currency.rate'].sudo().search([('currency_id', '=', o_payment_method.journal_id.currency_id.id)],order='name desc', limit=1)[0].rate
            else:
                rate_other_pay[o_payment_method.id] = 1
            if (o_payment_method.id not in balance_start_pay):
                balance_start_pay[o_payment_method.id] = 0
        _logger.warning('balance_start_pay: %s', balance_start_pay)
        return {
            'orders_details': {
                'quantity': len(orders.filtered(lambda o: o.amount_total > 0.0)),
                'quantity_refund': len(orders.filtered(lambda o: o.amount_total < 0.0)),
                'amount': round(sum(orders.filtered(lambda o: o.amount_total > 0.0).mapped('amount_total')), 2),
                'amount_refund': round(sum(orders.filtered(lambda o: o.amount_total < 0.0).mapped('amount_total')), 2),
                'amount_foreign': round(sum(orders.filtered(lambda o: o.amount_total > 0.0).mapped('amount_total_foreign')), 2),
                'amount_refund_foreign': round(sum(orders.filtered(lambda o: o.amount_total < 0.0).mapped('amount_total_foreign')), 2)
            },
            'rate': rate,
            'payments_amount': round(sum(payments.mapped('amount')), 2),
            'payments_amount_foreign': payments_amount_foreign,
            'pay_later_amount': round(sum(pay_later_payments.mapped('amount')), 2),
            'pay_later_amount_foreign': pay_later_amount_foreign,
            'currency_format': {
                'id': self.config_id.show_currency.id,
                'symbol': self.config_id.show_currency.symbol,
                'position': self.config_id.show_currency.position,
                'rounding': self.config_id.show_currency.rounding,
                'decimals': self.config_id.show_currency.decimal_places
            },
            'opening_notes': self.opening_notes,
            'default_cash_details': {
                'name': default_cash_payment_method_id.name,
                'enable_currencies': default_cash_payment_method_id.enable_currencies,
                'amount': round(balance_start_pay[default_cash_payment_method_id.id] + total_default_cash_payment_amount + (cash_in_out[default_cash_payment_method_id.id] if (default_cash_payment_method_id.id in cash_in_out) else 0), 2),
                'opening': balance_start_pay[default_cash_payment_method_id.id],
                'payment_amount': round(total_default_cash_payment_amount, 2),
                'payment_amount_pay': round(total_default_cash_payment_amount_pay, 2),
                'payment_amount_change': round(total_default_cash_payment_amount_change, 2),
                'moves': cash_in_out_list[default_cash_payment_method_id.id] if (default_cash_payment_method_id.id in cash_in_out_list) else [],
                'currency_id': default_cash_payment_method_id.journal_id.currency_id.id if (default_cash_payment_method_id.journal_id.currency_id) else self.env.company.currency_id.id,
                'id': default_cash_payment_method_id.id,
            } if default_cash_payment_method_id else None,
            'non_cash_payment_methods': [{
                'name': pm.name,
                'enable_currencies': pm.enable_currencies,
                'amount': round(balance_start_pay[pm.id] + sum(orders.payment_ids.filtered(lambda p: (p.payment_method_id == pm) if (p.payment_method_id.type != 'pay_later') else (p.payment_method_id == pm and ((p.pos_order_id.order_credit != 'payment_contributions') or (p.pos_order_id.order_credit == 'payment_contributions' and  p.amount > 0)))).mapped('amount')), 2) if (pm.enable_currencies == False) else balance_start_pay[pm.id] + sum(orders.payment_ids.filtered(lambda p: (p.payment_method_id == pm) if (p.payment_method_id.type != 'pay_later') else (p.payment_method_id == pm and ((p.pos_order_id.order_credit != 'payment_contributions') or (p.pos_order_id.order_credit == 'payment_contributions' and  p.amount > 0))) ).mapped('amount_foreign')),
                'cash_box_out_move': cash_in_out[pm.id] if (pm.id in cash_in_out) else 0,
                'opening': balance_start_pay[pm.id],
                'number': len(orders.payment_ids.filtered(lambda p: p.payment_method_id == pm)),
                'moves': cash_in_out_list[pm.id] if (pm.type == 'cash' and pm.id in cash_in_out_list) else [],
                'currency_id': pm.journal_id.currency_id.id if (pm.journal_id.currency_id) else self.env.company.currency_id.id,
                'id': pm.id,
                'type': pm.type,
                'currency_format': {
                    'id': pm.journal_id.currency_id.id if (pm.journal_id.currency_id) else self.env.company.currency_id.id,
                    'symbol': pm.journal_id.currency_id.symbol if (pm.journal_id.currency_id) else self.env.company.currency_id.symbol,
                    'position': pm.journal_id.currency_id.position if (pm.journal_id.currency_id) else self.env.company.currency_id.position,
                    'rounding': pm.journal_id.currency_id.rounding if (pm.journal_id.currency_id) else self.env.company.currency_id.rounding,
                    'decimals': pm.journal_id.currency_id.decimal_places if (pm.journal_id.currency_id) else self.env.company.currency_id.decimal_places
                },
                'rate': rate_other_pay[pm.id],
                'payment_amount': round((sum(payments.filtered(lambda p: p.payment_method_id == pm).mapped('amount'))/rate_other_pay[pm.id]), 2) if (pm.enable_currencies == False) else sum(payments.filtered(lambda p: p.payment_method_id == pm).mapped('amount_foreign')),
                'payment_amount_origin': round((sum(payments.filtered(lambda p: p.payment_method_id == pm).mapped('amount')))),
                'payment_amount_pay': round((sum(payments.filtered(lambda p: (p.payment_method_id == pm and p.amount > 0)).mapped('amount'))/rate_other_pay[pm.id]), 2) if (pm.enable_currencies == False) else sum(payments.filtered(lambda p: (p.payment_method_id == pm and p.amount > 0)).mapped('amount_foreign')),
                'payment_amount_change': round((sum(payments.filtered(lambda p: (p.payment_method_id == pm and p.amount < 0)).mapped('amount'))/rate_other_pay[pm.id]), 2) if (pm.enable_currencies == False) else sum(payments.filtered(lambda p: (p.payment_method_id == pm and p.amount < 0)).mapped('amount_foreign'))
            } for pm in other_payment_method_ids],
            'is_manager': self.env.user.has_group("point_of_sale.group_pos_manager"),
            'amount_authorized_diff': self.config_id.amount_authorized_diff if self.config_id.set_maximum_difference else None
        }

    def post_closing_cash_details_payment_method(self, defaultCash, nonCashPaymentMethods, paymentsCountedCash):
        self.ensure_one()
        #cash_register_temp = self.cash_register_id
        paymentMethod = self.env['pos.payment.method'].sudo().search([('id', '=', defaultCash['id'])],order='name desc', limit=1)[0]
        #accountBankStatement = self.env['account.bank.statement'].sudo().search([('pos_session_id', '=', self.id), ('journal_id', '=', paymentMethod.journal_id.id)],order='name desc', limit=1)[0]
        #self.cash_register_id = accountBankStatement
        statement_id = self.statement_ids.filtered(lambda st: st.journal_id.id == paymentMethod.journal_id.id)
        check_closing_session = self._cannot_close_session()
        if check_closing_session:
            return check_closing_session
        if not statement_id:
            # The user is blocked anyway, this user error is mostly for developers that try to call this function
            raise UserError(_("There is no cash register in this session."))
        #self.cash_register_id.balance_end_real = paymentsCountedCash[str(defaultCash['id'])]['counted']
        statement_id.balance_end = defaultCash['payment_amount']
        statement_id.balance_end_real = float(paymentsCountedCash[str(defaultCash['id'])]['counted'].replace('.','').replace(',','.'))
        counted_cash = 0.0
        for otherPayment in nonCashPaymentMethods:
            if otherPayment['type'] == 'cash':
                paymentMethod = self.env['pos.payment.method'].sudo().search([('id', '=', otherPayment['id'])],order='name desc', limit=1)[0]
                #accountBankStatement = self.env['account.bank.statement'].sudo().search([('pos_session_id', '=', self.id), ('journal_id', '=', paymentMethod.journal_id.id)],order='name desc', limit=1)[0]
                #self.cash_register_id = accountBankStatement
                statement_id = self.statement_ids.filtered(lambda st: st.journal_id.id == paymentMethod.journal_id.id)
                check_closing_session = self._cannot_close_session()
                if check_closing_session:
                    return check_closing_session
                if not statement_id:
                    # The user is blocked anyway, this user error is mostly for developers that try to call this function
                    raise UserError(_("There is no cash register in this session."))
                #self.cash_register_id.balance_end_real = paymentsCountedCash[str(otherPayment['id'])]['counted']
                statement_id.balance_end = otherPayment['payment_amount']
                statement_id.balance_end_real = float(paymentsCountedCash[str(otherPayment['id'])]['counted'].replace('.','').replace(',','.'))
                if (otherPayment['enable_currencies']):
                    rate = self.env['res.currency.rate'].search([('company_id','=', self.company_id.id), ('currency_id', '=', otherPayment['currency_id']), ('name', '<=', self.start_at)], limit=1).rate
                    counted_cash = counted_cash + (round((statement_id.balance_end_real / rate), 2))
                else:
                    counted_cash = counted_cash + (statement_id.balance_end_real)
        #self.cash_register_id = cash_register_temp
        counted_cash = counted_cash + float(paymentsCountedCash[str(defaultCash['id'])]['counted'].replace('.','').replace(',','.'))
        self.cash_register_balance_end_real = counted_cash
        return {'successful': True}

    @api.depends('payment_method_ids', 'order_ids', 'cash_register_balance_start', 'cash_register_balance_end_real')
    def _compute_cash_balance(self):
        for session in self:
            cash_payment_method = session.payment_method_ids.filtered('is_cash_count')
            if cash_payment_method:
                total_cash_payment = 0.0
                captured_cash_payments_domain = AND([session._get_captured_payments_domain(),[('payment_method_id', 'in', cash_payment_method.ids)]])
                result = self.env['pos.payment']._read_group(captured_cash_payments_domain, aggregates=['amount:sum'])
                total_cash_payment = result[0][0] or 0.0
                if session.state == 'closed':
                    total_cash = session.cash_real_transaction + total_cash_payment
                else:
                    total_cash = sum(session.statement_line_ids.mapped('amount')) + total_cash_payment
                session.cash_register_balance_end = session.cash_register_balance_start + total_cash
                session.cash_register_difference = session.cash_register_balance_end_real - session.cash_register_balance_end
            else:
                session.cash_register_balance_end = 0.0
                session.cash_register_difference = 0.0
    
    def _create_cash_statement_lines_and_cash_move_lines(self, data):
        MoveLine = data.get('MoveLine')
        split_receivables_cash = data.get('split_receivables_cash')
        combine_receivables_cash = data.get('combine_receivables_cash')
		#_logger.warning('_create_cash_statement_lines_and_cash_move_lines-split_receivables_cash: %s', split_receivables_cash)
		#_logger.warning('_create_cash_statement_lines_and_cash_move_lines-combine_receivables_cash: %s', combine_receivables_cash)
		# handle split cash payments
        split_cash_statement_line_vals = []
        split_cash_receivable_vals = []
        for payment, amounts in split_receivables_cash.items():
            #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-split_receivables_cash-payment: %s', payment)
            #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-split_receivables_cash-amounts: %s', amounts)
            journal_id = payment.payment_method_id.journal_id.id
			#_logger.warning('_create_cash_statement_lines_and_cash_move_lines-journal_id: %s', journal_id)
            if (payment.payment_method_id.enable_currencies):
				#_logger.warning('_create_cash_statement_lines_and_cash_move_lines-P1-rate: %s', rate)
                amounts['amount'] = payment.amount_foreign
                #amounts['amount_converted'] = payment.amount_foreign
                #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-split_receivables_cash-amounts(F): %s', amounts)
            split_cash_statement_line_vals.append(
                self._get_split_statement_line_vals(
                    journal_id,
                    amounts['amount'],
                    payment
                )
            )
            split_cash_receivable_vals.append(
                self._get_split_receivable_vals(
                    payment,
                    amounts['amount'],
                    amounts['amount_converted']
                )
            )
			#_logger.warning('_create_cash_statement_lines_and_cash_move_lines-split_cash_statement_line_vals: %s', split_cash_statement_line_vals)
			#_logger.warning('_create_cash_statement_lines_and_cash_move_lines-split_cash_receivable_vals: %s', split_cash_receivable_vals)
		# handle combine cash payments
        combine_cash_statement_line_vals = []
        combine_cash_receivable_vals = []
        payment_method_convert = {}
        for payment_method, amounts in combine_receivables_cash.items():
            #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-combine_receivables_cash-payment_method: %s', payment_method)
            #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-combine_receivables_cash-amounts: %s', amounts)
            #if (payment_method.enable_currencies):
            payment_method_convert[payment_method.journal_id.id] = {
                'enable_currencies': payment_method.enable_currencies,
                'amount': amounts['amount'],
                'amount_foreign': amounts['amount_foreign'],
            }
            #raise UserError('Error')
            if not float_is_zero(amounts['amount'] , precision_rounding=self.currency_id.rounding):
                '''if (payment_method.enable_currencies):
                    amounts['amount'] = amounts['amount_foreign']
                    _logger.warning('_create_cash_statement_lines_and_cash_move_lines-P2-new(amount): %s', amounts['amount'])'''
                combine_cash_statement_line_vals.append(
                    self._get_combine_statement_line_vals(
                        payment_method.journal_id.id,
                        amounts['amount'],
                        payment_method
                    )
                )
                combine_cash_receivable_vals.append(
                    self._get_combine_receivable_vals(
                        payment_method,
                        amounts['amount'],
                        amounts['amount_converted']
                    )
                )
			#_logger.warning('_create_cash_statement_lines_and_cash_move_lines-payment: %s', payment)
			#_logger.warning('_create_cash_statement_lines_and_cash_move_lines-amounts: %s', amounts)
		# create the statement lines and account move lines
        BankStatementLine = self.env['account.bank.statement.line']
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-BankStatementLine: %s', BankStatementLine)
        split_cash_statement_lines = {}
        combine_cash_statement_lines = {}
        split_cash_receivable_lines = {}
        combine_cash_receivable_lines = {}
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-create-split_cash_statement_line_vals: %s', split_cash_statement_line_vals)
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-create-combine_cash_statement_line_vals: %s', combine_cash_statement_line_vals)
        split_cash_statement_lines = BankStatementLine.create(split_cash_statement_line_vals).mapped('move_id.line_ids').filtered(lambda line: line.account_id.account_type == 'asset_receivable')
        combine_cash_statement_lines = BankStatementLine.create(combine_cash_statement_line_vals).mapped('move_id.line_ids').filtered(lambda line: line.account_id.account_type == 'asset_receivable')
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-split_cash_statement_lines: %s', split_cash_statement_lines)
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-combine_cash_statement_lines: %s', combine_cash_statement_lines)
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-payment_method_convert: %s', payment_method_convert)
        if (combine_cash_statement_lines):
            #_logger.warning('combine_cash_statement_lines-payment_method_convert: %s', payment_method_convert[combine_cash_statement_lines.move_id.line_ids[0].journal_id.id])
            #if (payment_method_convert[combine_cash_statement_lines.move_id.line_ids[0].journal_id.id]['enable_currencies']):
            for aml in combine_cash_statement_lines.move_id.line_ids:
                #_logger.warning('combine_cash_statement_lines-aml.amount_currency: %s', aml.amount_currency)
                #_logger.warning('combine_cash_statement_lines-aml.debit: %s', aml.debit)
                #_logger.warning('combine_cash_statement_lines-aml.credit: %s', aml.credit)
                #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-payment_method_convert-journal_id: %s',  payment_method_convert[aml.journal_id.id])
                if (payment_method_convert[aml.journal_id.id]['enable_currencies'] == True):
                    if aml.amount_currency > 0:
                        aml.debit = payment_method_convert[aml.journal_id.id]['amount']
                    if aml.amount_currency < 0:
                        aml.credit = payment_method_convert[aml.journal_id.id]['amount']
                    aml.amount_currency =  payment_method_convert[aml.journal_id.id]['amount_foreign'] * (1 if (aml.amount_currency > 0) else (-1))
                #_logger.warning('combine_cash_statement_lines-F-aml: %s', aml)
                #_logger.warning('combine_cash_statement_lines-F-aml.amount_currency: %s', aml.amount_currency)
                #_logger.warning('combine_cash_statement_lines-F-aml.debit: %s', aml.debit)
                #_logger.warning('combine_cash_statement_lines-F-aml.credit: %s', aml.credit)
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-BankStatementLine(F): %s', BankStatementLine)
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-create-split_cash_statement_lines: %s', split_cash_statement_lines)
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-create-combine_cash_statement_lines: %s', combine_cash_statement_lines)
        split_cash_receivable_lines = MoveLine.create(split_cash_receivable_vals)
        combine_cash_receivable_lines = MoveLine.create(combine_cash_receivable_vals)
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-split_cash_receivable_lines: %s', split_cash_receivable_lines)
        #_logger.warning('_create_cash_statement_lines_and_cash_move_lines-combine_cash_receivable_lines: %s', combine_cash_receivable_lines)
        data.update({'split_cash_statement_lines':	split_cash_statement_lines,
            'combine_cash_statement_lines':  combine_cash_statement_lines,
            'split_cash_receivable_lines':   split_cash_receivable_lines,
            'combine_cash_receivable_lines': combine_cash_receivable_lines
        })
        return data

    def _create_bank_payment_moves(self, data):
        combine_receivables_bank = data.get('combine_receivables_bank')
        split_receivables_bank = data.get('split_receivables_bank')
        bank_payment_method_diffs = data.get('bank_payment_method_diffs')
        MoveLine = data.get('MoveLine')
        payment_method_to_receivable_lines = {}
        payment_to_receivable_lines = {}
        for payment_method, amounts in combine_receivables_bank.items():
            #_logger.warning('_create_bank_payment_moves-P1-payment_method: %s', payment_method)
            #_logger.warning('_create_bank_payment_moves-P1-amounts: %s', amounts)
			#_logger.warning('_create_bank_payment_moves-P1-pm(currency_id): %s', payment_method.journal_id.currency_id)
			#_logger.warning('_create_bank_payment_moves-P1-pm(currency_id): %s', self.env.company.currency_id.id)
            amounts_cur = amounts['amount']
            amount_converted_cur = amounts['amount_converted']
            if (payment_method.enable_currencies):
                amounts['amount'] = amounts['amount_foreign']
                amounts_cur = amounts['amount']
				#_logger.warning('_create_bank_payment_moves-P2-new(amount): %s', amounts['amount'])

			#Linea de comision
            if (payment_method.enable_commission == True):
                amounts_commission = { 'amount': (amounts_cur * (payment_method.rate_commission/100)), 'amount_converted': (amount_converted_cur * (payment_method.rate_commission/100)) }
                amounts['amount'] = amounts['amount'] - amounts_commission['amount']
                amounts['amount_converted'] = amounts['amount_converted'] - amounts_commission['amount_converted']
				#print('_create_payment_moves-amounts(commission): ', amounts)

			#Linea de ISLR
            if (payment_method.enable_islr == True):
                amounts_islr = { 'amount': (amounts_cur * (payment_method.rate_islr/100)), 'amount_converted': (amount_converted_cur * (payment_method.rate_islr/100)) }
                amounts['amount'] = amounts['amount'] - amounts_islr['amount']
                amounts['amount_converted'] = amounts['amount_converted'] - amounts_islr['amount_converted']
				#print('_create_payment_moves-amounts(islr): ', amounts)

            combine_receivable_line = MoveLine.create(self._get_combine_receivable_vals(payment_method, amounts['amount'], amounts['amount_converted']))
            #_logger.info('_create_bank_payment_moves-combine_receivable_line: %s', combine_receivable_line)
			#Linea de comision
            if (payment_method.enable_commission == True):
                commission_receivable_line = MoveLine.create(self._get_combine_receivable_vals_custom(payment_method, 'Comision', payment_method.default_account_commission_id, amounts_commission['amount'], amounts_commission['amount_converted']))

			#Linea de ISLR
            if (payment_method.enable_islr == True):
                islr_receivable_line = MoveLine.create(self._get_combine_receivable_vals_custom(payment_method, 'ISLR', payment_method.default_account_islr_id, amounts_islr['amount'], amounts_islr['amount_converted']))

            payment_receivable_line = self._create_combine_account_payment(payment_method, amounts, diff_amount=bank_payment_method_diffs.get(payment_method.id) or 0)
            #_logger.info('_create_bank_payment_moves-payment_receivable_line: %s', payment_receivable_line)

            if ((payment_method.enable_commission == False) and (payment_method.enable_islr == False)):
                payment_method_to_receivable_lines[payment_method] = combine_receivable_line | payment_receivable_line
            if ((payment_method.enable_commission == True) and (payment_method.enable_islr == False)):
                payment_method_to_receivable_lines[payment_method] = combine_receivable_line | payment_receivable_line | commission_receivable_line
            if ((payment_method.enable_commission == False) and (payment_method.enable_islr == True)):
                payment_method_to_receivable_lines[payment_method] = combine_receivable_line | payment_receivable_line | islr_receivable_line
            if ((payment_method.enable_commission == True) and (payment_method.enable_islr == True)):
                payment_method_to_receivable_lines[payment_method] = combine_receivable_line | payment_receivable_line | commission_receivable_line | islr_receivable_line
		#_logger.warning('_create_bank_payment_moves-split_receivables_bank: %s', split_receivables_bank)
        for payment, amounts in split_receivables_bank.items():
            #_logger.warning('_create_bank_payment_moves-split_receivables_bank-payment: %s', payment)
            #_logger.warning('_create_bank_payment_moves-split_receivables_bank-payment_method_id: %s', payment.payment_method_id)
            _logger.warning('_create_bank_payment_moves-split_receivables_bank-amounts: %s', amounts)
            #if (payment.payment_method_id.enable_currencies):
                #amounts['amount'] = payment.amount_foreign
                #amounts['amount_converted'] = payment.amount_foreign
            #_logger.warning('_create_split_account_payment-_get_split_receivable_vals: %s', self._get_split_receivable_vals(payment, amounts['amount'], amounts['amount_converted']))
            split_receivable_line = MoveLine.create(self._get_split_receivable_vals(payment, amounts['amount'], amounts['amount_converted']))
            #_logger.warning('_create_split_account_payment-split_receivable_line: %s', split_receivable_line)
            payment_receivable_line = self._create_split_account_payment(payment, amounts)
            #_logger.warning('_create_split_account_payment-payment_receivable_line: %s', payment_receivable_line)
            if (payment.payment_method_id.enable_currencies):
                for aml in payment_receivable_line.move_id.line_ids:
                    #_logger.warning('_create_split_account_payment-aml.amount_currency: %s', aml.amount_currency)
                    aml.amount_currency = (amounts['amount_foreign'] if (amounts['amount_foreign'] > 0) else (amounts['amount_foreign'] * (-1))) * (1 if (aml.amount_currency > 0) else (-1))
                    #_logger.warning('_create_split_account_payment-aml.debit: %s', aml.debit)
                    #_logger.warning('_create_split_account_payment-aml.credit: %s', aml.credit)
                    if aml.debit != 0:
                        aml.debit = amounts['amount'] if (amounts['amount'] > 0) else (amounts['amount'] * (-1))
                    if aml.credit != 0:
                        aml.credit = amounts['amount'] if (amounts['amount'] > 0) else (amounts['amount'] * (-1))
            payment_to_receivable_lines[payment] = split_receivable_line | payment_receivable_line
            #_logger.warning('_create_split_account_payment-payment_to_receivable_lines[payment]: %s', payment_to_receivable_lines[payment])
            #raise UserError(_("No cash statement found for this session. Unable to record returned."))

        for bank_payment_method in self.payment_method_ids.filtered(lambda pm: pm.type == 'bank' and pm.split_transactions):
            self._create_diff_account_move_for_split_payment_method(bank_payment_method, bank_payment_method_diffs.get(bank_payment_method.id) or 0)

		#_logger.info('_create_bank_payment_moves-payment_to_receivable_lines: %s', payment_to_receivable_lines)
        data['payment_method_to_receivable_lines'] = payment_method_to_receivable_lines
        data['payment_to_receivable_lines'] = payment_to_receivable_lines
		#_logger.info('_create_bank_payment_moves-data: %s', data)
        return data
    
    def _get_combine_receivable_vals_custom(self, payment_method, typeName, account_id, amount, amount_converted):
        partial_vals = {
            'account_id': account_id.id,
            'move_id': self.move_id.id,
            'name': '%s - %s - %s' % (self.name, payment_method.name, typeName)
        }
        return self._debit_amounts(partial_vals, amount, amount_converted)

    '''def _reconcile_account_move_lines(self, data):
		# reconcile cash receivable lines
        split_cash_statement_lines = data.get('split_cash_statement_lines')
        combine_cash_statement_lines = data.get('combine_cash_statement_lines')
        split_cash_receivable_lines = data.get('split_cash_receivable_lines')
        combine_cash_receivable_lines = data.get('combine_cash_receivable_lines')
        combine_inv_payment_receivable_lines = data.get('combine_inv_payment_receivable_lines')
        split_inv_payment_receivable_lines = data.get('split_inv_payment_receivable_lines')
        combine_invoice_receivable_lines = data.get('combine_invoice_receivable_lines')
        split_invoice_receivable_lines = data.get('split_invoice_receivable_lines')
        stock_output_lines = data.get('stock_output_lines')
        payment_method_to_receivable_lines = data.get('payment_method_to_receivable_lines')
        payment_to_receivable_lines = data.get('payment_to_receivable_lines')

        all_lines = (
            split_cash_statement_lines
            | combine_cash_statement_lines
            | split_cash_receivable_lines
            | combine_cash_receivable_lines
        )
        all_lines.filtered(lambda line: line.move_id.state != 'posted').move_id._post(soft=False)

        accounts = all_lines.mapped('account_id')
        lines_by_account = [all_lines.filtered(lambda l: l.account_id == account and not l.reconciled) for account in accounts if account.reconcile]
        for lines in lines_by_account:
            lines.with_context(no_cash_basis=True).reconcile()

        for payment_method, lines in payment_method_to_receivable_lines.items():
            receivable_account = self._get_receivable_account(payment_method)
            if receivable_account.reconcile:
                lines.filtered(lambda line: not line.reconciled).with_context(no_cash_basis=True).reconcile()
        for payment, lines in payment_to_receivable_lines.items():
            if payment.partner_id.property_account_receivable_id.reconcile:
                lines.filtered(lambda line: not line.reconciled).with_context(no_cash_basis=True).reconcile()

		# Reconcile invoice payments' receivable lines. But we only do when the account is reconcilable.
		# Though `account_default_pos_receivable_account_id` should be of type receivable, there is currently
		# no constraint for it. Therefore, it is possible to put set a non-reconcilable account to it.
        if self.company_id.account_default_pos_receivable_account_id.reconcile:
            for payment_method in combine_inv_payment_receivable_lines:
                lines = combine_inv_payment_receivable_lines[payment_method] | combine_invoice_receivable_lines.get(payment_method, self.env['account.move.line'])
                lines.filtered(lambda line: not line.reconciled).with_context(no_cash_basis=True).reconcile()
            for payment in split_inv_payment_receivable_lines:
                lines = split_inv_payment_receivable_lines[payment] | split_invoice_receivable_lines.get(payment, self.env['account.move.line'])
                lines.filtered(lambda line: not line.reconciled).with_context(no_cash_basis=True).reconcile()

		# reconcile stock output lines
        pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
        pickings |= self.order_ids.filtered(lambda o: not o.is_invoiced).mapped('picking_ids')
        stock_moves = self.env['stock.move'].search([('picking_id', 'in', pickings.ids)])
        stock_account_move_lines = self.env['account.move'].search([('stock_move_id', 'in', stock_moves.ids)]).mapped('line_ids')
        for account_id in stock_output_lines:
            ( stock_output_lines[account_id]
            | stock_account_move_lines.filtered(lambda aml: aml.account_id == account_id)
            ).filtered(lambda aml: not aml.reconciled).with_context(no_cash_basis=True).reconcile()
        return data'''

    def show_cash_register(self):
        return {
            'name': _('Caja registradora'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement',
            'view_mode': 'list,kanban',
            'domain': [('pos_session_id', '=', self.id)],
        }
        