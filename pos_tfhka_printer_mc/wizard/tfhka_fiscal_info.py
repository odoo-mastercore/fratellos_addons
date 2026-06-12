# -*- coding: utf-8 -*-
################################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class TfhkaFiscalInfo(models.TransientModel):
    _name = "tfhka.fiscal.info.wizard"
    _description = "Informacion fiscal TFHKA"

    pos_order_id  = fields.Many2one('pos.order', string="Pedido", readonly=True)
    fiscal_invoice_number = fields.Char(string='Número de factura fiscal', help="Fiscal invoice number issued by TFHKA.")
    printer_serial = fields.Char(string='Serial de la impresora', help="Printer serial.")
    partner_id = fields.Many2one('res.partner', string='Cliente', related='pos_order_id.partner_id', readonly=True)
    currency_id = fields.Many2one('res.currency', related='pos_order_id.currency_id', string="Moneda", readonly=True)
    amount_tax = fields.Monetary(string='IVA', related='pos_order_id.amount_tax', readonly=True)
    amount_total = fields.Monetary(string='Total', related='pos_order_id.amount_total', readonly=True)

    def action_save_info_tfhka(self):
        if (self.fiscal_invoice_number == ''):
            raise UserError(_("Debe indicar el numero de factura fiscal."))
        if (self.printer_serial == ''):
            raise UserError(_("Debe indicar el serial de la impresora fiscal."))
        data = {}
        data['type_document_printer'] = ('invoice' if (self.amount_total > 0.0) else 'credit_note')
        if (data['type_document_printer'] == 'invoice'):
            data['lastInvoiceNumber'] = self.fiscal_invoice_number
            data['lastNCNumber'] = False
        else:
            data['lastNCNumber'] = self.fiscal_invoice_number
            data['lastInvoiceNumber'] = False
        data['registeredMachineNumber'] = self.printer_serial
        self.pos_order_id.set_fiscal_invoice_number(self.pos_order_id.access_token, (1 if (self.amount_total > 2) else 'credit_note'), data)
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('¡Informacion de la factura acutalizada!'),
                    'type': 'success',
                    'message': _('Los datos de la factura fueron actualizados correctamente.'),
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_window_close',
                    }
                }
            }