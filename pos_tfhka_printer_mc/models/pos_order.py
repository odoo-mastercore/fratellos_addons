# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2020-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
import base64
from odoo import fields, models, tools, api, _
from odoo.tools import formatLang, float_is_zero
from odoo.modules.module import get_resource_path
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang
import logging
_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _name = 'pos.order'
    _inherit = ['pos.order', 'mail.thread', 'mail.activity.mixin']

    fiscal_invoice_number = fields.Char(string='Número de factura fiscal', help="Fiscal invoice number issued by TFHKA.", tracking=True)
    type_document_printer = fields.Selection(selection=[
        ('invoice', 'Factura'),
        ('credit_note', 'Nota de credito'),
        ('debit_note', 'Nota de debito')], string='Tipo de documento', readonly=False)
    printer_serial = fields.Char(string='Serial de la impresora', help="Printer serial.", tracking=True)
    show_update_fiscal = fields.Boolean('Visualizar boton de Actualizacion de datos fiscales', compute='_compute_show_update_fiscal')
    is_tax_box = fields.Boolean('Caja fiscal', readonly=False, related='config_id.is_tax_box')

    _sql_constraints = [
        ('name_fiscal_invoice_number_uniq', 'unique(fiscal_invoice_number, type_document_printer, printer_serial)', 'Numero documento fiscal ya se encuentra registrado para esa impresora!'),
    ]

    def set_fiscal_invoice_number(self, access_token, action, data):
        constraints_order = self.env['pos.order'].search([('fiscal_invoice_number', '=', data[('lastInvoiceNumber' if (action == 1) else 'lastNCNumber')]), ('type_document_printer', '=', ('invoice' if (action == 1) else 'credit_note')), ('printer_serial', '=',data['registeredMachineNumber'])])
        if (len(constraints_order) == 0):
            order = self.env['pos.order'].search([('access_token', '=', access_token)])
            if (len(order) > 0):
                res = order[0].write({ 'fiscal_invoice_number': data[('lastInvoiceNumber' if (action == 1) else 'lastNCNumber')], 'type_document_printer': ('invoice' if (action == 1) else 'credit_note'), 'printer_serial': data['registeredMachineNumber'] })
                if (len(order[0].account_move)):
                    order[0].account_move[0].write({ 'fiscal_invoice_number': (str(data[('lastInvoiceNumber' if (action == 1) else 'lastNCNumber')])), 'printer_serial': data['registeredMachineNumber'] })
                    return {
                        'code': '00',
                        'description': 'Actualizacion completada',
                    }
                else:
                    return {
                        'code': '03',
                        'description': 'No se encontro la Factura indicada para el token de acceso: ' + access_token,
                    }
            else:
                return {
                    'code': '02',
                    'description': 'No se encontro la orden indicada para el token de acceso: ' + access_token,
                }
        else:
            return {
                'code': '01',
                'description': 'Numero documento fiscal ya se encuentra registrado para esa impresora, por favor verifique el estado del equipo y el aplicativo de comunicacion.',
            }

    def action_info_tfhka_wizard(self):
        return {
            'name': _('Actualizar datos fiscales'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tfhka.fiscal.info.wizard',
            'target': 'new',
            'context': { 'default_pos_order_id': self.id }
        }

    def _compute_show_update_fiscal(self):
        for record in self:
            self.show_update_fiscal = True if (record.config_id.is_tax_box == True and (record.fiscal_invoice_number == '' or record.fiscal_invoice_number == False)) else False

    def _generate_pos_order_invoice(self):
        res = super(PosOrder, self)._generate_pos_order_invoice()
        for record in self:
            if (record.config_id.is_tax_box == True and record.fiscal_invoice_number != ''):
                data = {}
                data['type_document_printer'] = ('invoice' if (record.amount_total > 0.0) else 'credit_note')
                if (data['type_document_printer'] == 'invoice'):
                    data['lastInvoiceNumber'] = record.fiscal_invoice_number
                    data['lastNCNumber'] = False
                else:
                    data['lastNCNumber'] = record.fiscal_invoice_number
                    data['lastInvoiceNumber'] = False
                data['registeredMachineNumber'] = record.printer_serial
                record.set_fiscal_invoice_number(record.access_token, (1 if (record.amount_total > 2) else 'credit_note'), data)
        return res