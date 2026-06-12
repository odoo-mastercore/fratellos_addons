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
from odoo.modules.module import get_resource_path
from odoo.exceptions import UserError, ValidationError
import hashlib

class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    demo_printer_tfhka = fields.Boolean(string='Imprimir demo en maquina fiscal', readonly=False, related='pos_config_id.demo_printer_tfhka')
    version_tfhka = fields.Selection(selection=[
        ('V8_5_0', 'PROTOCOLOS V8.5.0 (CC 199)'),
        ('VX_0_0', 'PROTOCOLOS VX.5.0 (CC 119)'),
        ('V1_SRP_812', 'PROTOCOLOS V1.01 SRP – 812 (CC NA)')], string='Versión', readonly=False, related='pos_config_id.version_tfhka')
    time_printer_tfhka_doc = fields.Integer('Tiempo de espera por linea para impresion de documentos', readonly=False, related='pos_config_id.time_printer_tfhka_doc')
    time_printer_tfhka_rep_z = fields.Integer('Tiempo de espera para impresion de reporte Z', readonly=False, related='pos_config_id.time_printer_tfhka_rep_z')
    printer_tfhka_flag_21 =  fields.Selection(selection=[
        ('00_8_2', 'FLAG 21 (00) 8E 2D'),
        ('00_7_3', 'FLAG 21 (01) 7E 3D'),
        ('00_6_4', 'FLAG 21 (02) 6E 4D'),
        ('00_9_1', 'FLAG 21 (11) 9E 1D'),
        ('00_10_0', 'FLAG 21 (12) 10E 0D'),
        ('30_14_2', 'FLAG 21 (30) 14E 2D')], string='Formato de precio (FLAG 21)', readonly=False, related='pos_config_id.printer_tfhka_flag_21')
    #calculate_tax_base_product_price = fields.Boolean(string='Calcular base imponible del precio del producto.', readonly=False, related='pos_config_id.calculate_tax_base_product_price')
    #add_tax_product_price = fields.Boolean(string='Incluir IVA al precio del producto.', readonly=False, related='pos_config_id.add_tax_product_price')
    calculate_product_price_tfhka = fields.Selection(selection=[
        ('default', 'Por defecto'),
        ('tax_base', 'Calcular base imponible del precio del producto'),
        ('add_tax', 'Incluir IVA al precio del producto')], string='Modificador de precio del producto', readonly=False, related='pos_config_id.calculate_product_price_tfhka')
    block_new_order_if_not_been_issued_invoice = fields.Boolean('Bloquear nuevo pedido si no se ha emitido factura', readonly=False, related='pos_config_id.block_new_order_if_not_been_issued_invoice')
    is_tax_box = fields.Boolean('Caja fiscal', readonly=False, related='pos_config_id.is_tax_box')
    printing_invoice_automatic = fields.Boolean('Impresión automática de factura fiscal', readonly=False, related='pos_config_id.printing_invoice_automatic')
    add_additional_information_header = fields.Boolean('Agregar informacion adicional en encabezado de factura', readonly=False, related='pos_config_id.add_additional_information_header')
    additional_information_header = fields.Text('Informacion del encabezado', readonly=False, related='pos_config_id.additional_information_header')
    add_additional_information_footer = fields.Boolean('Agregar informacion adicional en pie de factura', readonly=False, related='pos_config_id.add_additional_information_footer')
    additional_information_footer = fields.Text('Informacion del pie', readonly=False, related='pos_config_id.additional_information_footer')
    url_access = fields.Char('URL de acceso', readonly=False, related='pos_config_id.url_access')
    user_access = fields.Char('Usuario de acceso', readonly=False, related='pos_config_id.user_access')
    password_access = fields.Char('Contraseña de acceso', readonly=False, related='pos_config_id.password_access')
    url_access_base = fields.Char('URL de base de acceso', readonly=False, related='pos_config_id.url_access_base')
    user_access_base = fields.Char('Usuario de base de acceso', readonly=False, related='pos_config_id.user_access_base')
    password_access_base = fields.Char('Contraseña de base de acceso', readonly=False, related='pos_config_id.password_access_base')

    @api.onchange('url_access_base')
    def _onchange_url_access_base(self):
        for record in self:
            if (record.url_access_base):
                record.url_access = hashlib.sha256(record.url_access_base.encode('utf-8')).hexdigest()
                record.pos_config_id.write({ 'url_access': record.url_access })

    @api.onchange('user_access_base')
    def _onchange_user_access_base(self):
        for record in self:
            if (record.user_access_base):
                record.user_access = hashlib.sha256(record.user_access_base.encode('utf-8')).hexdigest()

    @api.onchange('password_access_base')
    def _onchange_password_access_base(self):
        for record in self:
            if (record.password_access_base):
                record.password_access = hashlib.sha256(record.password_access_base.encode('utf-8')).hexdigest()