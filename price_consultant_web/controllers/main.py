# -*- coding: utf-8 -*-
###############################################################################
# Author: SINAPSYS GLOBAL SA || MASTERCORE SAS
# Copyleft: 2021-Present.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
#
#
###############################################################################

import logging
import ast
import json
from odoo import http, _
from odoo.http import Controller, request

_logger = logging.getLogger(__name__)


class PriceConsultant(Controller):

    @http.route(['/consultant'], type='http', auth='user', website=True)
    def product_consultant(self, **kwargs):
        return request.render("price_consultant_web.price_consultant_template", {})

    @http.route('/consultant/product/search', type='http', auth="user", methods=['POST'], website=True, csrf=False)
    def balance_pay_search(self, barcode, **kw):
        res = {'found': False}
        # pricelist_ids = False
        # Verificar que las Tarifas existan para Moneda principal y en Divisas
        pricelist_currency = request.env['product.pricelist'].sudo().search([
            ('currency_id', '=', request.env.company.currency_id.id),
            ('company_id', '=', request.env.company.id),
            ('enabled_price_consultant', '=', True)
        ], limit=1)
        if not pricelist_currency:
            self.msg_log(barcode, "Moneda principal no encontrada")
            return json.dumps(res)
        pricelist_foreign_currency = request.env['product.pricelist'].sudo().search([
            ('currency_id', '=', request.env.company.foreign_currency_id.id),
            ('company_id', '=', request.env.company.id),
            ('enabled_price_consultant', '=', True)
        ], limit=1)
        if not pricelist_foreign_currency:
            self.msg_log(barcode, "Moneda en divisas no encontrada")
            return json.dumps(res)
        # pricelist_ids = [[pricelist_currency, pricelist_foreign_currency]]

        # Buscamos el producto
        product = request.env['product.product'].sudo().search([
            ('barcode', '=', str(barcode).strip()),
            ('company_id', '=', request.env.company.id)
        ],limit=1)
        if not product:
            # Buscamos el producto sin company
            product = request.env['product.product'].sudo().search([
                ('barcode', '=', str(barcode).strip())
            ],limit=1)
        if not product:
            self.msg_log(barcode, "Producto no encontrado")
            return json.dumps(res)

        price = pricelist_currency._get_product_price(product, 1)
        taxes = [0.0, 0.0]
        tax_id = product.taxes_id.filtered(lambda x: x.company_id.id == request.env.company.id)
        total = price
        image = '/price_consultant_web/static/src/consultant_price/src/images/placeholder_image.png'
        if product.image_1920:
            image = '/web/image/product.product/%s/image_1024' % (product.id)
        if tax_id and tax_id.amount:
            price_with_tax = price * (1 + (tax_id.amount / 100))
            amount_tax = (tax_id.amount / 100) * price
            taxes = [tax_id.amount, amount_tax]
            price = price
            total = price_with_tax

        price_currency = pricelist_foreign_currency._get_product_price(product, 1)
        if tax_id and tax_id.amount:
            price_currency = price_currency * (1 + (tax_id.amount / 100))
        res.update({
            'found': True,
            'name': product.name,
            'currency': ['VEF' if pricelist_currency.currency_id.symbol == 'Bs.' else pricelist_currency.currency_id.name, pricelist_currency.currency_id.symbol],
            'foreign_currency': [pricelist_foreign_currency.currency_id.name, pricelist_foreign_currency.currency_id.symbol],
            'price': price,
            'tax': taxes,
            'total': total,
            'price_currency': price_currency,
            'alt_price': 0.0,
            'image': image
        })
        if 'list_secondary_price_total' in product._fields:
            if product.list_secondary_price_total:
                res.update({
                    'alt_price': product.list_secondary_price_total
                })
        return json.dumps(res)

    def msg_log(self, barcode, body):
        _logger.error("**** **** **** ****")
        _logger.error("Consultor de precios - barcode(%s): %s" % (barcode, body))
        _logger.error("**** **** **** ****")