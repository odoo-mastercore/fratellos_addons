# -*- coding: utf-8 -*-
##############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2022-Present.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import hashlib

class posConfig(models.Model):
    _inherit = 'pos.config'

    demo_printer_tfhka = fields.Boolean('Imprimir demo en maquina fiscal', default=False)
    version_tfhka = fields.Selection(selection=[
        ('V8_5_0', 'PROTOCOLOS V8.5.0 (CC 199)'),
        ('VX_0_0', 'PROTOCOLOS VX.0.0 (CC 119)'),
        ('V1_SRP_812', 'PROTOCOLOS V1.01 SRP – 812 (CC NA)')], string='Versión', readonly=False, default='V8_5_0')
    time_printer_tfhka_doc = fields.Integer('Tiempo de espera por linea para impresion de documentos', default=750)
    time_printer_tfhka_rep_z = fields.Integer('Tiempo de espera para impresion de reporte Z', default=15000)
    printer_tfhka_flag_21 =  fields.Selection(selection=[
        ('00_8_2', 'FLAG 21 (00) 8E 2D'),
        ('00_7_3', 'FLAG 21 (01) 7E 3D'),
        ('00_6_4', 'FLAG 21 (02) 6E 4D'),
        ('00_9_1', 'FLAG 21 (11) 9E 1D'),
        ('00_10_0', 'FLAG 21 (12) 10E 0D'),
        ('30_14_2', 'FLAG 21 (30) 14E 2D')], string='Formato de precio (FLAG 21)', readonly=False, default='00_8_2')
    #calculate_tax_base_product_price = fields.Boolean(string='Calcular base imponible del precio del producto.', default=False)
    calculate_product_price_tfhka = fields.Selection(selection=[
        ('default', 'Por defecto'),
        ('tax_base', 'Calcular base imponible del precio del producto'),
        ('add_tax', 'Incluir IVA al precio del producto')], string='Modificador de precio del producto', readonly=False, default='default')
    #add_tax_product_price = fields.Boolean(string='Incluir IVA al precio del producto.', default=False)
    block_new_order_if_not_been_issued_invoice = fields.Boolean('Bloquear nuevo pedido, si no se ha emitido factura', default=True)
    is_tax_box = fields.Boolean('Caja fiscal', default=True)
    printing_invoice_automatic = fields.Boolean('Impresión automática de factura fiscal', default=False)
    add_additional_information_header = fields.Boolean('Agregar informacion adicional en encabezado de factura', default=False)
    additional_information_header = fields.Text('Informacion del encabezado')
    add_additional_information_footer = fields.Boolean('Agregar informacion adicional en pie de factura', default=False)
    additional_information_footer = fields.Text('Informacion del pie')
    url_access_base = fields.Char('URL de base de acceso')
    url_access = fields.Char('URL de acceso')
    user_access_base = fields.Char('Usuario de base de acceso')
    user_access = fields.Char('Usuario de acceso')
    password_access_base = fields.Char('Contraseña de base de acceso')
    password_access = fields.Char('Contraseña de acceso')