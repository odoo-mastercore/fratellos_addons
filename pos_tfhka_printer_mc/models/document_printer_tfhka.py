# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2020-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
from odoo import models, fields, api
from datetime import date, timedelta, datetime
import logging
_logger = logging.getLogger(__name__)

class DocumentPrinterTfhka(models.Model):
    _name = "document.printer.tfhka"
    _description = "Impresora fiscal - Documentos"

    invoice_date = fields.Datetime(string='Fecha del documento', readonly=False)
    serial_printer = fields.Char(string='Serial de la impresora', readonly=False)
    type_document_printer = fields.Selection(selection=[
        ('invoice', 'Factura'),
        ('credit_note', 'Nota de credito'),
        ('debit_note', 'Nota de debito')], string='Tipo de documento', readonly=False)
    invoice_name = fields.Char(string='Nro de documento', readonly=False)
    invoice_name_origin = fields.Char(string='Nro de documento de origen', readonly=False)
    invoice_date_origin = fields.Date(string='Fecha del documento de origen', readonly=False)
    serial_printer_origin = fields.Char(string='Serial de la impresora de origen', readonly=False)
    vat = fields.Char(string='Doc identificacion', readonly=False)
    partner_name = fields.Char(string='Nombre del cliente', readonly=False)
    invoice_bi_ex = fields.Float(string='Exento', readonly=False)
    invoice_tax_p = fields.Float(string='Percibido', readonly=False)
    invoice_bi_g = fields.Float(string='BI General', readonly=False)
    invoice_tax_g = fields.Float(string='Iva General', readonly=False)
    invoice_bi_r = fields.Float(string='BI Reducido', readonly=False)
    invoice_tax_r = fields.Float(string='Iva Reducido', readonly=False)
    invoice_bi_a = fields.Float(string='BI Adicional', readonly=False)
    invoice_tax_a = fields.Float(string='Iva Adicional', readonly=False)
    invoice_bi_igtf = fields.Float(string='BI IGTF', readonly=False)
    invoice_tax_igtf = fields.Float(string='Iva IGTF', readonly=False)
    invoice_bi_t = fields.Float(string='BI Total', readonly=False)
    invoice_tax_t = fields.Float(string='Iva Total', readonly=False)
    invoice_total = fields.Float(string='Total', readonly=False)

    _sql_constraints = [
        ('number_report_z_uniq', 'unique(registeredMachineNumber, numberOfLastZReport, type_document_printer)', 'Documento ya se encuentra registrado para esa impresora!'),
    ]

    #ORM
    def mapped_create(self, data):
        print('mapped_create-data: ', data)
        documentPrinter = []
        for line in data['message']:
            doc_validate = self.env['document.printer.tfhka'].search([('type_document_printer', '=', data['type_document_printer']), ('serial_printer', '=', line['serial_printer']), ('invoice_name', '=', line['invoice_name'])])
            if (len(doc_validate) == 0):
                invoiceDate = datetime.strptime((line['invoice_date'] + ' ' + line['invoice_time']), '%d-%m-%Y %H:%M').date()
                invoiceDateOrigin = (datetime.strptime((line['invoice_date_origin'].replace('/','-')), '%d-%m-%Y').date() if ('invoice_date_origin' in line) else False)
                document = {
                    'invoice_date': str(invoiceDate.strftime('%Y-%m-%d %H:%M')),
                    'serial_printer': (line['serial_printer'] if ('serial_printer' in line) else  False),
                    'type_document_printer': (data['type_document_printer'] if ('type_document_printer' in data) else  False),
                    'invoice_name': (line['invoice_name'] if ('invoice_name' in line) else False),
                    'invoice_name_origin': (line['invoice_name_origin'] if ('invoice_name_origin' in line) else False),
                    'invoice_date_origin': (str(invoiceDateOrigin.strftime('%Y-%m-%d %H:%M')) if (invoiceDateOrigin != False) else False),
                    'serial_printer_origin': (line['serial_printer_origin'] if ('serial_printer_origin' in line) else  False),
                    'vat': (line['vat'] if ('vat' in line) else  False),
                    'partner_name': (line['partner_name'] if ('partner_name' in line) else  False),
                    'invoice_bi_ex': (line['invoice_bi_ex'] if ('invoice_bi_ex' in line) else  False),
                    'invoice_tax_p': (line['invoice_tax_p'] if ('invoice_tax_p' in line) else  False),
                    'invoice_bi_g': (line['invoice_bi_g'] if ('invoice_bi_g' in line) else  False),
                    'invoice_tax_g': (line['invoice_tax_g'] if ('invoice_tax_g' in line) else  False),
                    'invoice_bi_r': (line['invoice_bi_r'] if ('invoice_bi_r' in line) else  False),
                    'invoice_tax_r': (line['invoice_tax_r'] if ('invoice_tax_r' in line) else  False),
                    'invoice_bi_a': (line['invoice_bi_a'] if ('invoice_bi_a' in line) else  False),
                    'invoice_tax_a': (line['invoice_tax_a'] if ('invoice_tax_a' in line) else  False),
                    'invoice_bi_igtf': (line['invoice_bi_igtf'] if ('invoice_bi_igtf' in line) else  False),
                    'invoice_tax_igtf': (line['invoice_tax_igtf'] if ('invoice_tax_igtf' in line) else  False),
                    'invoice_bi_t': (line['invoice_bi_t'] if ('invoice_bi_t' in line) else  False),
                    'invoice_tax_t': (line['invoice_tax_t'] if ('invoice_tax_t' in line) else  False),
                    'invoice_total': (line['invoice_total'] if ('invoice_total' in line) else  False),
                }
                self.env['document.printer.tfhka'].create(document)
                documentPrinter.append(document)
            else:
                _logger.warning('Documento ya se encuentra registrado para esa impresora!')
        return documentPrinter