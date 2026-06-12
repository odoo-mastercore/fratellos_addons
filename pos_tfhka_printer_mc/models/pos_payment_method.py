# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2020-Present.
# License LGPL-3.0 or later (http: //www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    code_in_printer_tfhka =  fields.Selection(selection=[
        ('01', '01'),
        ('02', '02'),
        ('03', '03'),
        ('04', '04'),
        ('05', '05'),
        ('06', '06'),
        ('07', '07'),
        ('08', '08'),
        ('09', '09'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
        ('13', '13'),
        ('14', '14'),
        ('15', '15'),
        ('16', '16'),
        ('17', '17'),
        ('18', '18'),
        ('19', '19'),
        ('20', '20'),
        ('21', '21'),
        ('22', '22'),
        ('23', '23'),
        ('24', '24')], string='Codigo del metodo de pago en la impresora THFKA')

    @api.onchange('code_in_printer_tfhka')
    def _onchange_code_in_printer_tfhka(self):
        for record in self:
            if (record.code_in_printer_tfhka != False):
                if ('is_igtf' in record):
                    if (record.is_igtf == False and (float(record.code_in_printer_tfhka) > 19)):
                        record.code_in_printer_tfhka = False
                        raise ValidationError(_("Codigo reservado para metodos de pago con IGTF activo, debe indicar un codigo correspondiente al rango 01-19."))
                    if (record.is_igtf == True and (float(record.code_in_printer_tfhka) < 20)):
                        record.code_in_printer_tfhka = False
                        raise ValidationError(_("Codigo reservado para metodos de pago sin IGTF activo, debe indicar un codigo correspondiente al rango 20-24."))
                else:
                    if (float(record.code_in_printer_tfhka) > 19):
                        record.code_in_printer_tfhka = False
                        raise ValidationError(_("Codigo reservado para metodos de pago con IGTF activo, debe indicar un codigo correspondiente al rango 01-19."))

    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('code_in_printer_tfhka')
        return res