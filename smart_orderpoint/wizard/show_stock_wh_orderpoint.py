# -*- coding: utf-8 -*-
##############################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2021-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
###############################################################################
import math
from odoo import api, fields, models,_

from odoo.exceptions import UserError

class ShowStockWhOrderpointWizard(models.TransientModel):
    _name = 'stock.wh.orderpoint'
    _description = 'Show Stock Warehouse OrderPoint'

    stock_wh_orderpoint_ids = fields.One2many('stock.wh.orderpoint.line', inverse_name='stock_wh_op_id')

    def action_generate(self):
        for rec in self.stock_wh_orderpoint_ids:
            if not rec.company_id.company_inter_sale_id or not rec.company_id.company_inter_sale_id.id:
                raise UserError(_('''La empresa "%s" no contiene los diarios de ventas y/o compras en res.config.settings, 
                                  por favor comuniquese con el Administrador del sistema.''',rec.company_id.name))
            
            orderpoints_send = self.stock_wh_orderpoint_ids.search([
                                                                ('stock_wh_op_id','=',self.id),
                                                                ('product_id','=',rec.product_id.id),
                                                                ('action','=','send')])
                
            orderpoints_receive = self.stock_wh_orderpoint_ids.search([
                                                            ('stock_wh_op_id','=',self.id),
                                                            ('product_id','=',rec.product_id.id),
                                                            ('action','=','receive')])
            print(orderpoints_send)
            print(orderpoints_receive)
            if not len(orderpoints_send)==1 :
                raise UserError(_('Hay más de un envío para un mismo producto o no existe un envío para algún producto'))
            
            if len(orderpoints_receive)==0:
                raise UserError(_('No existe la opción de recibir para algún producto especifico'))
            if rec.action =='send':
                order_sale={
                    'partner_id': orderpoints_receive[0].company_id.partner_id.id,
                    'date_order': fields.Datetime.now(),
                    'company_inter': True,
                    'company_id':rec.company_id.id,
                    'order_line': [(0,0,{
                        'product_id': rec.product_id.id,
                        'product_uom_qty': rec.quantity,
                    })]
                }
                sale = self.env['sale.order'].sudo().create(order_sale)
                sale.sudo().action_confirm()
                #sale.sudo()._create_invoices(final=True)
            elif rec.action == 'receive':
                ratio = rec.product_id.uom_po_id.ratio
                qty_to_order = math.ceil(rec.quantity/ratio)
                #get_qty_entre_ratio = math.ceil(qty_to_order/ratio)
                #get_qty_entre_ratio_by_ratio = math.ceil(get_qty_entre_ratio*ratio)
                order_purchase={
                    'partner_id': orderpoints_send.company_id.partner_id.id,
                    'date_order': fields.Datetime.now(),
                    'company_inter': True,
                    'company_id':rec.company_id.id,
                    'order_line': [(0,0,{
                        'product_id': rec.product_id.id,
                        'product_qty': qty_to_order,
                    })]
                }
                purchase = self.env['purchase.order'].sudo().create(order_purchase)
                purchase.sudo().button_confirm()
                picking = self.env['stock.picking'].sudo().search([('origin','=',purchase.name)])
                picking.sudo().action_confirm()
                #picking.sudo().action_set_quantities_to_reservation()
                #picking.sudo().button_validate()
                #purchase.sudo().action_create_invoice()
        message = "Las transacciónes intercompañías se han creado exitosamente, ¡felicidades!"
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': message,
                    'img_url': '/web/static/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        return True
        

class StockWhOrderpointLine(models.TransientModel):
    _name = 'stock.wh.orderpoint.line'
    _description = 'Stock Warehouse OrderPoint Line'

    product_id = fields.Many2one('product.product', string="Producto")
    location_id = fields.Many2one('stock.location', string="Lugar")
    company_id = fields.Many2one('res.company', string="Compañía")
    qty_on_hand = fields.Integer(string="Cantidad a Mano")
    stock_wh_op_id = fields.Many2one('stock.wh.orderpoint')
    action = fields.Selection([
        ('send', 'Enviar'),
        ('receive', 'Recibir')], default='send', string='Acción')
    quantity = fields.Integer(string='Cantidad')    
