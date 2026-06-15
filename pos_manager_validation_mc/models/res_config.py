# -*- coding: utf-8 -*-
################################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
################################################################################
import base64
from odoo import fields, models, tools, api
from odoo.modules.module import get_resource_path

class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    close_pos = fields.Boolean(readonly=False, related='pos_config_id.close_pos')
    order_delete = fields.Boolean(readonly=False, related='pos_config_id.order_delete')
    order_line_delete = fields.Boolean(readonly=False, related='pos_config_id.order_line_delete')
    qty_detail = fields.Boolean(readonly=False, related='pos_config_id.qty_detail')
    discount_app = fields.Boolean(readonly=False, related='pos_config_id.discount_app')
    disabled_discount_app = fields.Boolean( readonly=False, related='pos_config_id.disabled_discount_app')
    payment_perm = fields.Boolean(readonly=False, related='pos_config_id.payment_perm')
    price_change = fields.Boolean(readonly=False, related='pos_config_id.price_change')
    disabled_price_change = fields.Boolean(readonly=False, related='pos_config_id.disabled_price_change')
    move_in_out_cash = fields.Boolean(readonly=False, related='pos_config_id.move_in_out_cash')
    restrict_pos_product_category_active = fields.Boolean(related='pos_config_id.restrict_pos_product_category_active', readonly=False)
    pos_product_category_restrict_ids = fields.Many2many('pos.category', 'pos_category_restrict_rel',
        'pos_config_id', 'pos_category_id',  related='pos_config_id.pos_product_category_restrict_ids', readonly=False)
    restrict_cash_opening = fields.Boolean(readonly=False, related='pos_config_id.restrict_cash_opening')
    restrict_pos_payment_method_active = fields.Boolean(readonly=False, related='pos_config_id.restrict_pos_payment_method_active')
    pos_payment_method_restrict_ids = fields.Many2many('pos.payment.method', 'pos_payment_method_restrict_rel',
        'pos_config_id', 'pos_payment_method_id',  readonly=False, related='pos_config_id.pos_payment_method_restrict_ids')
    return_orders = fields.Boolean( readonly=False, related='pos_config_id.return_orders')
    set_fiscal_position = fields.Boolean(readonly=False, related='pos_config_id.set_fiscal_position')
    set_pricelist_product = fields.Boolean( readonly=False, related='pos_config_id.set_pricelist_product')
    hide_pricelist_foreign_currency = fields.Boolean(readonly=False, related='pos_config_id.hide_pricelist_foreign_currency')

    '''@api.onchange('disabled_discount_app')
    def _onchange_disabled_discount_app(self):
        if (self.disabled_discount_app == True):
            self.discount_app = False

    @api.onchange('discount_app')
    def _onchange_discount_app(self):
        if (self.disabled_discount_app == True):
            self.discount_app = False

    @api.onchange('disabled_price_change')
    def _onchange_disabled_price_change(self):
        if (self.disabled_price_change == True):
            self.price_change = False

    @api.onchange('price_change')
    def _onchange_price_change(self):
        if (self.disabled_price_change == True):
            self.price_change = False'''