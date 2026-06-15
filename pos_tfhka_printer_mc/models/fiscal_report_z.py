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

class FiscalReportZ(models.Model):
    _name = "fiscal.report.z"
    _description = "Reporte Z"

    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    config_id = fields.Many2one('pos.config', string='Terminal Punto de Venta')
    pos_session_id = fields.Many2one('pos.session', string='Sesión')
    zReportDate = fields.Datetime(string='Fecha del reporte Z', readonly=False, help="Report date Z")
    registeredMachineNumber = fields.Char(string='Serial de la impresora', readonly=False, help="Printer serial.")
    numberOfLastZReport = fields.Integer(string='Número del reporte', readonly=False, help="Report number.")

    freeSalesTax = fields.Float(string='Ventas exentas', readonly=False, help="Exempt sales.")
    freeTaxDevolution = fields.Float(string='Exento NC', readonly=False, help="Exempt N Credit.")
    freeTaxDebit = fields.Float(string='Exento ND', readonly=False, help="Exempt N Debit.")

    generalRate1Sale = fields.Float(string='Base G Ventas', readonly=False, help="General tax base sales.")
    generalRate1Tax = fields.Float(string='Iva G Ventas', readonly=False, help="General tax value.")
    generalRateDevolution = fields.Float(string='Base G NC', readonly=False, help="Base G NC.")
    generalRateTaxDevolution = fields.Float(string='Iva G NC', readonly=False, help="Iva G NC.")
    generalRateDebit = fields.Float(string='Base G ND', readonly=False, help="Base G ND.")
    generalRateTaxDebit = fields.Float(string='Iva G ND', readonly=False, help="Iva G ND.")

    reducedRate2Sale = fields.Float(string='Base R Ventas', readonly=False, help="Reduce tax base sales.")
    reducedRate2Tax = fields.Float(string='Iva R Ventas', readonly=False, help="Reduce tax value.")
    reducedRateDevolution = fields.Float(string='Base R NC', readonly=False, help="Base R NC.")
    reducedRateTaxDevolution = fields.Float(string='Iva R NC', readonly=False, help="Iva R NC.")
    reducedRateDebit = fields.Float(string='Base R ND', readonly=False, help="Base R ND.")
    reducedRateTaxDebit = fields.Float(string='Iva R ND', readonly=False, help="Iva R ND.")

    additionalRate3Sal = fields.Float(string='Base A Ventas', readonly=False, help="Additional tax base sales.")
    additionalRate3Tax = fields.Float(string='Iva A Ventas', readonly=False, help="Additional tax value.")
    additionalRateDevolution = fields.Float(string='Base A NC', readonly=False, help="Base A NC.")
    additionalRateTaxDevolution = fields.Float(string='Iva A NC', readonly=False, help="Iva A NC.")
    additionalRateDebit = fields.Float(string='Base A ND', readonly=False, help="Base A ND.")
    additionalRateTaxDebit = fields.Float(string='Iva A ND', readonly=False, help="Iva A ND.")

    lastInvoiceDate = fields.Datetime(string='Fecha/Hora ult factura', readonly=False, help="Last invoice date/time.")
    numberOfLastInvoice = fields.Char(string='Ultima Factura emitida', readonly=False, help="Last invoice issued.")
    numberOfLastCreditNote = fields.Char(string='Ultima NC', readonly=False, help="Last credit note issued.")
    numberOfLastDebitNote = fields.Char(string='Ultima ND', readonly=False, help="Last debit note issued.")
    numberOfLastNonFiscal = fields.Char(string='Ultimo DNF', readonly=False, help="Last document non fiscal issued.")

    taxBaseSalesIgtf = fields.Float(string='Base Ventas IGTF', readonly=False, help="Tax Base Sales Igtf.")
    taxSalesReceiptIgtf = fields.Float(string='Iva Ventas IGTF', readonly=False, help="Tax Sales Receipt Igtf.")
    valueSalesIgtf = fields.Float(string='Valor Ventas Igtf', readonly=False, help="Additional tax base sales.")

    taxBaseCreditIgtf = fields.Float(string='Base NC IGTF', readonly=False, help="Tax Base Credit Note Igtf.")
    taxCreditReceiptIgtf = fields.Float(string='Iva NC IGTF', readonly=False, help="Tax Credit Note Receipt Igtf.")
    valueCreditIgtf = fields.Float(string='Valor NC Igtf', readonly=False, help="Additional tax base Credit Note.")

    taxBaseDebitIgtf = fields.Float(string='Base ND IGTF', readonly=False, help="Tax Base Credit Debit Igtf.")
    taxDebitReceiptIgtf = fields.Float(string='Iva ND IGTF', readonly=False, help="Tax Credit Debit Receipt Igtf.")
    valueDebitIgtf = fields.Float(string='Valor ND Igtf', readonly=False, help="Additional tax base Credit Debit.")

    total_base_charged = fields.Float(string='Total Base', readonly=False, help="otal base charged.")
    full_tax_value = fields.Float(string='Total IVA', readonly=False, help="Full tax value.")
    total_charged = fields.Float(string='Total Bs', readonly=False, help="Total charged.")

    total_base_charged_nc = fields.Float(string='Total Base NC', readonly=False, help="Total base charged NC.")
    full_tax_value_nc = fields.Float(string='Total IVA NC', readonly=False, help="Full tax value NC.")
    total_charged_nc = fields.Float(string='Total Bs NC', readonly=False, help="Total charged NC.")

    total_base_charged_nd = fields.Float(string='Total Base ND', readonly=False, help="Total base charged ND.")
    full_tax_value_nd = fields.Float(string='Total IVA ND', readonly=False, help="Full tax value ND.")
    total_charged_nd = fields.Float(string='Total Bs ND', readonly=False, help="Total charged ND.")

    _sql_constraints = [
        ('number_report_z_uniq', 'unique(registeredMachineNumber, numberOfLastZReport)', 'Numero Reporte Z ya se encuentra registrado para esa impresora!'),
    ]

    #ORM
    def mapped_create(self, data):
        returnData = []
        for line in data['message']:
            report_z = self.env['fiscal.report.z'].search([('registeredMachineNumber', '=', data['registeredMachineNumber']), ('numberOfLastZReport', '=', line['numberOfLastZReport'])])
            if (len(report_z) == 0):
                zReportDate = datetime.strptime((line['zReportDate'] + ' ' + line['zReportTime']), '%d-%m-%Y %H:%M').date()
                lastInvoiceDate = datetime.strptime((line['lastInvoiceDate'] + ' ' + line['lastInvoiceTime']), '%d-%m-%Y %H:%M').date()
                taxReportZ = {
                    'zReportDate' : str(zReportDate.strftime('%Y-%m-%d %H:%M')) or False,
                    'registeredMachineNumber' : (data['registeredMachineNumber'] if ('registeredMachineNumber' in data) else False),
                    'pos_session_id' : (data['pos_session_id'] if ('pos_session_id' in data) else False),
                    'numberOfLastZReport' : (line['numberOfLastZReport'] if ('numberOfLastZReport' in line) else False),
                    'freeSalesTax' : (line['freeSalesTax'] if ('freeSalesTax' in line) else False),
                    'freeTaxDevolution' : (line['freeTaxDevolution'] if ('freeTaxDevolution' in line) else False),
                    'freeTaxDebit' : (line['freeTaxDebit'] if ('freeTaxDebit' in line) else False),
                    'generalRate1Sale' : (line['generalRate1Sale'] if ('generalRate1Sale' in line) else False),
                    'generalRate1Tax' : (line['generalRate1Tax'] if ('generalRate1Tax' in line) else False),
                    'generalRateDevolution' : (line['generalRateDevolution'] if ('generalRateDevolution' in line) else False),
                    'generalRateTaxDevolution' : (line['generalRateTaxDevolution'] if ('generalRateTaxDevolution' in line) else False),
                    'generalRateDebit' : (line['generalRateDebit'] if ('generalRateDebit' in line) else False),
                    'generalRateTaxDebit' : (line['generalRateTaxDebit'] if ('generalRateTaxDebit' in line) else False),
                    'reducedRate2Sale' : (line['reducedRate2Sale'] if ('reducedRate2Sale' in line) else False),
                    'reducedRate2Tax' : (line['reducedRate2Tax'] if ('reducedRate2Tax' in line) else False),
                    'reducedRateDevolution' : (line['reducedRateDevolution'] if ('reducedRateDevolution' in line) else False),
                    'reducedRateTaxDevolution' : (line['reducedRateTaxDevolution'] if ('reducedRateTaxDevolution' in line) else False),
                    'reducedRateDebit' : (line['reducedRateDebit'] if ('reducedRateDebit' in line) else False),
                    'reducedRateTaxDebit' : (line['reducedRateTaxDebit'] if ('reducedRateTaxDebit' in line) else False),
                    'additionalRate3Sal' : (line['additionalRate3Sal'] if ('additionalRate3Sal' in line) else False),
                    'additionalRate3Tax' : (line['additionalRate3Tax'] if ('additionalRate3Tax' in line) else False),
                    'additionalRateDevolution' : (line['additionalRateDevolution'] if ('additionalRateDevolution' in line) else False),
                    'additionalRateTaxDevolution' : (line['additionalRateTaxDevolution'] if ('additionalRateTaxDevolution' in line) else False),
                    'additionalRateDebit' : (line['additionalRateDebit'] if ('additionalRateDebit' in line) else False),
                    'additionalRateTaxDebit' : (line['additionalRateTaxDebit'] if ('additionalRateTaxDebit' in line) else False),
                    'lastInvoiceDate': lastInvoiceDate or False,
                    'numberOfLastInvoice' : (line['numberOfLastInvoice'] if ('numberOfLastInvoice' in line) else False),
                    'numberOfLastCreditNote' : (line['numberOfLastCreditNote'] if ('numberOfLastCreditNote' in line) else False),
                    'numberOfLastDebitNote' : (line['numberOfLastDebitNote'] if ('numberOfLastDebitNote' in line) else False),
                    'numberOfLastNonFiscal' : (line['numberOfLastNonFiscal'] if ('numberOfLastNonFiscal' in line) else False),
                    'taxBaseSalesIgtf' : (line['taxBaseSalesIgtf'] if ('taxBaseSalesIgtf' in line) else False),
                    'taxSalesReceiptIgtf' : (line['taxSalesReceiptIgtf'] if ('taxSalesReceiptIgtf' in line) else False),
                    'valueSalesIgtf' : (line['valueSalesIgtf'] if ('valueSalesIgtf' in line) else False),
                    'taxBaseCreditIgtf' : (line['taxBaseCreditIgtf'] if ('taxBaseCreditIgtf' in line) else False),
                    'taxCreditReceiptIgtf' : (line['taxCreditReceiptIgtf'] if ('taxCreditReceiptIgtf' in line) else False),
                    'valueCreditIgtf' : (line['valueCreditIgtf'] if ('valueCreditIgtf' in line) else False),
                    'taxBaseDebitIgtf' : (line['taxBaseDebitIgtf'] if ('taxBaseDebitIgtf' in line) else False),
                    'taxDebitReceiptIgtf' : (line['taxDebitReceiptIgtf'] if ('taxDebitReceiptIgtf' in line) else False),
                    'valueDebitIgtf' : (line['valueDebitIgtf'] if ('valueDebitIgtf' in line) else False),
                    'full_tax_value' : ((line['generalRate1Tax'] if ('generalRate1Tax' in line) else 0.0) + (line['reducedRate2Tax'] if ('reducedRate2Tax' in line) else 0.0) + (line['additionalRate3Tax'] if ('additionalRate3Tax' in line) else 0.0)),
                    'total_base_charged' : ((line['freeSalesTax'] if ('freeSalesTax' in line) else 0.0) + (line['generalRate1Sale'] if ('generalRate1Sale' in line) else 0.0) + (line['reducedRate2Sale'] if ('reducedRate2Sale' in line) else 0.0) + (line['additionalRate3Sal'] if ('additionalRate3Sal' in line) else 0.0)),
                    'total_charged' : ((line['generalRate1Tax'] if ('generalRate1Tax' in line) else 0.0) + (line['reducedRate2Tax'] if ('reducedRate2Tax' in line) else 0.0) + (line['additionalRate3Tax'] if ('additionalRate3Tax' in line) else 0.0) + (line['freeSalesTax'] if ('freeSalesTax' in line) else 0.0) + (line['generalRate1Sale'] if ('generalRate1Sale' in line) else 0.0) + (line['reducedRate2Sale'] if ('reducedRate2Sale' in line) else 0.0) + (line['additionalRate3Sal'] if ('additionalRate3Sal' in line) else 0.0)),
                    'full_tax_value_nc' : ((line['generalRateTaxDevolution'] if ('generalRateTaxDevolution' in line) else 0.0) + (line['reducedRateTaxDevolution'] if ('reducedRateTaxDevolution' in line) else 0.0) + (line['additionalRateTaxDevolution'] if ('additionalRateTaxDevolution' in line) else 0.0)),
                    'total_base_charged_nc' : ((line['freeTaxDevolution'] if ('freeTaxDevolution' in line) else 0.0) + (line['generalRateDevolution'] if ('generalRateDevolution' in line) else 0.0) + (line['reducedRateDevolution'] if ('reducedRateDevolution' in line) else 0.0) + (line['additionalRateDevolution'] if ('additionalRateDevolution' in line) else 0.0)),
                    'total_charged_nc' : ((line['generalRateTaxDevolution'] if ('generalRateTaxDevolution' in line) else 0.0) + (line['reducedRateTaxDevolution'] if ('reducedRateTaxDevolution' in line) else 0.0) + (line['additionalRateTaxDevolution'] if ('additionalRateTaxDevolution' in line) else 0.0) + (line['freeTaxDevolution'] if ('freeTaxDevolution' in line) else 0.0) + (line['generalRateDevolution'] if ('generalRateDevolution' in line) else 0.0) + (line['reducedRateDevolution'] if ('reducedRateDevolution' in line) else 0.0) + (line['additionalRateDevolution'] if ('additionalRateDevolution' in line) else 0.0)),
                    'full_tax_value_nd' : ((line['generalRateTaxDebit'] if ('generalRateTaxDebit' in line) else 0.0) + (line['reducedRateTaxDebit'] if ('reducedRateTaxDebit' in line) else 0.0) + (line['additionalRateTaxDebit'] if ('additionalRateTaxDebit' in line) else 0.0)),
                    'total_base_charged_nd' : ((line['freeTaxDebit'] if ('freeTaxDebit' in line) else 0.0) + (line['generalRateDebit'] if ('generalRateDebit' in line) else 0.0) + (line['reducedRateDebit'] if ('reducedRateDebit' in line) else 0.0) + (line['additionalRateDebit'] if ('additionalRateDebit' in line) else 0.0)),
                    'total_charged_nd' : ((line['generalRateTaxDebit'] if ('generalRateTaxDebit' in line) else 0.0) + (line['reducedRateTaxDebit'] if ('reducedRateTaxDebit' in line) else 0.0) + (line['additionalRateTaxDebit'] if ('additionalRateTaxDebit' in line) else 0.0) + (line['freeTaxDevolution'] if ('freeTaxDevolution' in line) else 0.0) + (line['freeTaxDebit'] if ('freeTaxDebit' in line) else 0.0) + (line['generalRateDebit'] if ('generalRateDebit' in line) else 0.0) + (line['reducedRateDebit'] if ('reducedRateDebit' in line) else 0.0) + (line['additionalRateDebit'] if ('additionalRateDebit' in line) else 0.0)),
                }
                if ('company_id' in data):
                    taxReportZ['company_id'] = data['company_id']
                if ('config_id' in data):
                    taxReportZ['config_id'] = data['config_id']
                self.env['fiscal.report.z'].create(taxReportZ)
                returnData.append(taxReportZ)
                _logger.warning('Numero Reporte Z ya se encuentra registrado para esa impresora!')
        return returnData