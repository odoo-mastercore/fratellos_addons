# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import fields, _, models, tools, api
from odoo.modules.module import get_resource_path

class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    pos_session_id = fields.Many2one('pos.session', string="Session", copy=False)
    config_id = fields.Many2one('pos.config', string='Point of Sale', index=True)
    payment_method_id = fields.Many2one('pos.payment.method', string='Método de pago caja registradora en TPV', copy=False)
    opening_balance = fields.Monetary(string='Saldo de apertura', store=True, readonly=False)
    opening_balance_default = fields.Float('Saldo de apertura en moneda de la compañia')

    @api.depends('line_ids.journal_id')
    def _compute_journal_id(self):
        for statement in self:
            if (statement.journal_id == False and len(statement.journal_id) == 0):
                super(AccountBankStatement, statement)._compute_journal_id()

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['id', 'name', 'pos_session_id', 'config_id', 'payment_method_id', 'opening_balance', 'currency_id', 'balance_start', 'balance_end', 'line_ids']

    @api.model
    def _load_pos_data_domain(self, data):
        return [('pos_session_id', '=', data['pos.session']['data'][0]['id'])]

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        return {
            'data': self.with_context({**self.env.context}).search_read(domain, fields, load=False),
            'fields': fields,
        }