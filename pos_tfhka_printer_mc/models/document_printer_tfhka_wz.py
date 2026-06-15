###############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2022-Present.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
import logging
import pprint
import json
import datetime
import requests
import uuid as uuid
import base64
import hashlib
from odoo import http, models
from odoo.http import request, Response #, JsonRequest
from odoo.tools import date_utils
from requests.auth import HTTPBasicAuth
from odoo import models, fields, api, _
from datetime import date, timedelta, datetime
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class DocumentPrinterTfhkaWz(models.Model):
    _name = 'document.printer.tfhka.wz'

    type_document_printer = fields.Selection(selection=[
        ('invoice', 'Factura'),
        ('credit_note', 'Nota de credito'),
        ('debit_note', 'Nota de debito'),
        ('report_z', 'Reporte Z')], string='Tipo de documento', default='invoice', readonly=False)
    type_action = fields.Selection(selection=[
        ('extraction', 'Extraccion'),
        ('reprint', 'Reimpresion')], string='Tipo de accion', default='extraction', readonly=False)
    type_search = fields.Selection(selection=[
        ('date', 'Fecha'),
        ('number', 'Nro de documento')], string='Tipo de busqueda', default='date', readonly=False)
    type_command = fields.Char('Comando', compute='_compute_type_command', store=True)
    start_doc = fields.Integer(string='Documento de inicio', required=True)
    end_doc = fields.Integer(string='Documento final', required=True)
    name = fields.Datetime('Fecha de generacion', default=datetime.now())
    user_id = fields.Many2one('res.users', string='Usuario', compute='_compute_user_id', store=True)
    serial_printer = fields.Char(string='Serial de la impresora')
    config_id = fields.Many2one('pos.config', string='TPV', compute='_compute_user_id', store=True)

    @api.depends('type_document_printer', 'type_action', 'type_search')
    def _compute_type_command(self):
        for record in self:
            if (record.type_action == 'extraction'):
                record.type_command = 'U4'
            else:
                record.type_command = 'R'
            if (record.type_document_printer == 'invoice'):
                record.type_command = record.type_command + ('f' if (record.type_search == 'date') else 'F')
            elif (record.type_document_printer == 'credit_note'):
                record.type_command = record.type_command + ('c' if (record.type_search == 'date') else 'C')
            elif (record.type_document_printer == 'debit_note'):
                record.type_command = record.type_command + ('d' if (record.type_search == 'date') else 'D')
            elif (record.type_document_printer == 'report_z'):
                record.type_command = record.type_command + ('z' if (record.type_search == 'date') else 'Z')

    def _compute_user_id(self):
        for record in self:
            record.user_id = self._context.get('uid')

    def _default_start_date(self):
        return datetime.now()

    start_date = fields.Date(string='Fecha de inicio', required=True, default=_default_start_date)
    end_date = fields.Date(string='Fecha fin', required=True, default=fields.Datetime.now)
    
    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    def action_printer(self):
        pass