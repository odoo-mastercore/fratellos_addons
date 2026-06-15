# -*- coding: utf-8 -*-
##############################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2021-Present.
# License OPL-1 (Odoo Proprietary License v1.0)
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
###############################################################################
from datetime import timedelta
from dateutil import relativedelta
import math
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models

import logging

_logger = logging.getLogger(__name__)

class stockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'
    _description = 'stock warehouse orderpoint inherit'

    # smart_orderpoint = fields.Boolean('Smart PrO',
    #     help="Punto de ReOrden Inteligente"
    # )
    trigger = fields.Selection(
        selection_add=[
            ('smartpro', 'SmartPro')
        ],
        ondelete={
            'smartpro': 'cascade'
        }
    )
    negotation_state = fields.Selection([
        ('draft', 'Sin negociacion'),
        ('warning','Mala negociacion'),
        ('success', 'Buena negociacion')] , 'Estado de la negociacion',default='draft', compute="_compute_negotation_state")
    date_from = fields.Date(string="Desde")
    date_to = fields.Date(string="Hasta")
    quantity_sale = fields.Integer(string="Vendido",
        compute="_compute_quantity_sale",
        help="Cantidad de producto vendido en el tiempo determinado")
    quantity_purchase = fields.Integer(string="Cantidad Comprada",
        compute="_compute_quantity_purchase",
        help="Cantidad de producto comprado en el tiempo determinado")
    ratio = fields.Float(string="Ratio",
        compute='_compute_ratio', store=True,
        help="Ratio de Rotacion del producto en el tiempo determinado")
    date_order = fields.Date(string="Días Proyección",
        help="Fecha estimada para la ejecuccion de la proyeccion de compra")
    sold_uc = fields.Float(string="Vendido x UC", compute="_compute_sold_uc", store=True)
    purchase_price = fields.Float(string='Precio de Compra')
    purchased_price = fields.Float(string='Precio Comprado', 
                                    compute='_compute_purchased_price',
                                    store=False)
    discount = fields.Float(string='Descuento %')
    uom_po_id = fields.Many2one('uom.uom', related='product_id.uom_po_id', string="Unidad de compra", readonly=False)
    qty_to_order_uom = fields.Float('Por Ordenar UC', compute='_compute_qty_to_order', inverse='_inverse_qty_to_order_uom', search='_search_qty_to_order', digits='Product Unit')

    # @api.depends('product_id')
    # def _compute_purchase_price(self):
    #     for rec in self:
    #         rec.purchase_price = 0
    #         supplier = rec.product_id.seller_ids
    #         if supplier:
    #             rec.purchase_price = supplier.mapped(lambda x:x.price if x.partner_id.id==self.env.company.id.partner_id.id else 0)

    @api.model
    def _cron_refresh_orderpoint_windows(self, only_smart=True, all_companies=False):
        """
        Corre a diario: ajusta ventanas de análisis y proyecta product_max_qty.
        - date_from: hoy - meses_historial (desde setting)
        - date_to:   hoy + 1 día
        - date_order: hoy + dias_proyeccion (desde setting)
        - Recalcula product_max_qty con la lógica del onchange (lado servidor).
        """
        today = fields.Date.context_today(self)

        domain = []
        if only_smart:
            domain.append(('trigger', '=', 'smartpro'))
        if not all_companies:
            domain.append(('company_id', '=', self.env.company.id))

        ops = self.sudo().search(domain)
        if not ops:
            _logger.info("[CRON Smart OP] No hay registros para actualizar (dominio: %s)", domain)
            return True

        # Agrupar por compañía para usar las configuraciones correspondientes
        ops_by_company = {}
        for op in ops:
            ops_by_company.setdefault(op.company_id, self.env['stock.warehouse.orderpoint'])
            ops_by_company[op.company_id] |= op

        updated = 0
        for company, company_ops in ops_by_company.items():
            months = company.smart_history_months
            days = company.smart_projection_days

            date_from = today - relativedelta(months=months)
            date_to = today + timedelta(days=1)
            date_order = today + timedelta(days=days)

            # 1) Ajustar ventanas de tiempo.
            company_ops.write({
                'date_from': date_from,
                'date_to': date_to,
                'date_order': date_order,
            })

            # 2) Forzar evaluación de computes usados (ratio depende de quantity_sale)
            #    Al acceder a 'ratio' Odoo lo computa si hace falta (store=True).
            for op in company_ops:
                ratio = float(op.ratio or 0.0)

                if op.date_order and op.date_to and op.date_order > op.date_to:
                    delta_days = (op.date_order - op.date_to).days
                else:
                    delta_days = 0

                new_max = round(ratio * (delta_days + 1), 0) if (delta_days > 0 and ratio) else 0.0
                # Usar qty_on_hand (stock físico) — el cliente genera OC manualmente,
                # por lo que no hay riesgo de doble compra. Coincide con la fórmula del Excel.
                if new_max:
                    gap = new_max - (op.qty_on_hand or 0.0)
                    new_max = gap if gap > 0.0 else 0.0

                # Escribe solo si cambia (menos escritura = más rápido)
                if (op.qty_to_order or 0.0) != new_max:
                    op.sudo().write({'qty_to_order': new_max})
                    updated += 1

        _logger.info("[CRON Smart OP] %s orderpoints ajustados; product_max_qty recalculado en %s registros", len(ops), updated)
        return True

    @api.model
    def _cron_generate_smart_orderpoints(self, limit=10000):
        """
        Genera reglas de reabastecimiento SmartPro para productos marcados
        con `include_orderpoint`.
        - Solo toma el primer almacén de cada compañía.
        - Evita duplicados por (product_id, location_id, company_id).
        """
        if 'include_orderpoint' not in self.env['product.product']._fields:
            _logger.warning("[CRON Smart OP] El campo include_orderpoint no existe en product.product")
            return True

        companies = self.env['res.company'].sudo().search([])
        total_created = 0

        for company in companies:
            warehouse = self.env['stock.warehouse'].sudo().search(
                [('company_id', '=', company.id)],
                order='id asc',
                limit=1,
            )
            if not warehouse or not warehouse.lot_stock_id:
                _logger.warning(
                    "[CRON Smart OP] Compañía %s sin warehouse/lot_stock configurado, se omite",
                    company.display_name,
                )
                continue

            products = self.env['product.product'].sudo().search([
                ('include_orderpoint', '=', False),
                ('active', '=', True),
            ],limit)
            if not products:
                _logger.warning(
                    "[CRON Smart OP] No se encontraron productos para la compañia: ",
                    company.name
                )
                continue

            location_id = warehouse.lot_stock_id.id
            existing_orderpoints = self.env['stock.warehouse.orderpoint'].sudo().search([
                ('company_id', '=', company.id),
                ('location_id', '=', location_id),
                ('product_id', 'in', products.ids),
                ('trigger', '=', 'smartpro')
            ])
            existing_product_ids = set(existing_orderpoints.mapped('product_id').ids)
            products_to_mark = self.env['product.product'].sudo()

            vals_list = []
            for product in products:
                if product.id in existing_product_ids:
                    products_to_mark |= product
                    continue
                vals_list.append({
                    'name': product.display_name,
                    'product_id': product.id,
                    'product_min_qty': 0.0,
                    'product_max_qty': 0.0,
                    'qty_multiple': 1.0,
                    'warehouse_id': warehouse.id,
                    'location_id': location_id,
                    'company_id': company.id,
                    'trigger': 'smartpro',
                })
                products_to_mark |= product

            if vals_list:
                self.env['stock.warehouse.orderpoint'].sudo().with_company(company).create(vals_list)
                total_created += len(vals_list)
            if products_to_mark:
                products_to_mark.include_orderpoint = True

        _logger.info("[CRON Smart OP] Reglas SmartPro creadas: %s", total_created)
        return True

    @api.depends('purchase_price', 'purchased_price')
    def _compute_negotation_state(self):
        for rec in self:
            rec.negotation_state = 'draft'
            if rec.purchase_price > rec.purchased_price:
                rec.negotation_state = 'warning'
            elif rec.purchase_price < rec.purchased_price:
                rec.negotation_state = 'success'

    @api.depends('product_id')
    def _compute_purchased_price(self):
        for rec in self:
            rec.purchased_price = 0.0
            if rec.product_id.standard_price:
                rec.purchased_price = rec.product_id.standard_price
            #if rec.product_id.seller_ids:
            #   rec.purchased_price = rec.product_id.seller_ids[-1].price

    @api.depends('quantity_sale','ratio')
    def _compute_sold_uc(self):
        for rec in self:
            ratio = rec.product_id.uom_po_id.ratio
            if not rec.product_id.uom_po_id.id == rec.product_id.uom_id.id:
                rec.sold_uc = rec.quantity_sale/ratio if ratio >0 else 0
            else:
                rec.sold_uc = rec.quantity_sale

    @api.depends('quantity_sale')
    def _compute_ratio(self):
        for rec in self:
            rec.ratio = 0
            if rec.date_from and rec.date_to and rec.date_to > rec.date_from:
                date = rec.date_to - rec.date_from
                rec.ratio = rec.quantity_sale / (date.days or 1)

    @api.onchange('date_to', 'date_order', 'date_from')
    @api.depends_context('company')
    def _onchange_qty_order(self):
        for rec in self:
            rec.qty_to_order_manual = 0
            rec.qty_to_order = 0
            date_today = fields.Date.today()
            if rec.date_to and rec.date_order and rec.date_order > rec.date_to:
                date = rec.date_order - date_today
                # Usar qty_on_hand (stock físico) para coincidir con la fórmula del Excel.
                # El cliente genera OC manualmente, no automáticamente.
                order = round(rec.ratio * (date.days), 0) - (rec.qty_on_hand or 0.0)
                if order > 0.00:
                    rec.qty_to_order = order
                    if (rec.product_id.uom_id.id != rec.product_id.uom_po_id.id):
                        rec.qty_to_order_uom = round((rec.qty_to_order / rec.product_id.uom_po_id.factor_inv), 0)
                    else:
                        rec.qty_to_order_uom = rec.qty_to_order

    @api.depends('date_from', 'date_to')
    def _compute_quantity_sale(self):
        for line in self:
            line.quantity_sale = 0
            date_from = line.date_from
            date_to = line.date_to
            if not (date_to and date_from and date_to > date_from):
                continue

            # FIX fecha: +1 día con < en lugar de <= para incluir todo el último día
            # (Odoo almacena stock.move.date con hora, un <= date_to corta a 00:00:00)
            date_to_exclusive = date_to + timedelta(days=1)

            # FIX rendimiento: read_group en vez de search+loop (1 query en lugar de N)
            base_domain = [
                ('product_id', '=', line.product_id.id),
                ('date', '>=', fields.Datetime.to_datetime(date_from)),
                ('date', '<', fields.Datetime.to_datetime(date_to_exclusive)),
                ('state', '=', 'done'),
                ('company_id', '=', line.company_id.id),
            ]

            # Salidas hacia clientes (ventas)
            out_result = self.env['stock.move'].read_group(
                base_domain + [
                    ('location_dest_id.usage', '=', 'customer'),
                    ('location_id', '=', line.location_id.id),
                ],
                ['product_qty:sum'], []
            )
            total_out = (out_result[0].get('product_qty') or 0.0) if out_result else 0.0

            # FIX devoluciones: entradas desde clientes de vuelta al almacén
            in_result = self.env['stock.move'].read_group(
                base_domain + [
                    ('location_id.usage', '=', 'customer'),
                    ('location_dest_id', '=', line.location_id.id),
                ],
                ['product_qty:sum'], []
            )
            total_in = (in_result[0].get('product_qty') or 0.0) if in_result else 0.0

            line.quantity_sale = max(0.0, total_out - total_in)

    @api.depends('date_from', 'date_to')
    def _compute_quantity_purchase(self):
        for line in self:
            line.quantity_purchase = 0
            date_from = line.date_from
            date_to = line.date_to
            if date_to and date_from and date_to > date_from:
                domain = [
                    ('product_id', '=', line.product_id.id),
                    ('date', '>=', date_from),
                    ('date', '<=', date_to),
                    ('state', '=', 'done'),
                    ('company_id', '=', line.company_id.id),
                    ('location_id.usage', '=', 'supplier')
                ]
                quantity_by_date = self.env['stock.move'].search(domain)
                total = 0.00
                if quantity_by_date:
                    for q in quantity_by_date:
                        total += q.product_qty
                    line.quantity_purchase = total

    def open_wizard(self):
        lines = []
        for rec in self:
            lines.append((0,0,
                {
                    'product_id': rec.product_id.id,
                    'company_id': rec.company_id.id,
                    'location_id': rec.location_id.id,
                    'qty_on_hand': rec.qty_on_hand
                }))
        view_id = self.env.ref('smart_orderpoint.view_show_stock_wh_orderpoint_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': (_("Reglas de Abastecimiento")),
            'res_model': 'stock.wh.orderpoint',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_stock_wh_orderpoint_ids': lines if lines else False,
            },
            'views': [(view_id, 'form')],
        }

    def _prepare_procurement_values(self, date=False, group=False):
        vals = super()._prepare_procurement_values(date=date, group=group)
        vals['purchase_price'] = self.purchase_price or self.purchased_price
        return vals

    @api.depends('qty_to_order_manual', 'qty_to_order_computed', 'date_to', 'date_order', 'ratio', 'qty_on_hand', 'qty_multiple')
    def _compute_qty_to_order(self):
        """
        Calcula qty_to_order en UC respetando edición manual:
        - Si existe qty_to_order_manual (!= 0), se usa ese valor.
        - Si no, usa el cálculo SmartPro.

        Usa qty_on_hand (stock físico) para coincidir exactamente con la fórmula
        del Excel del cliente: Demanda = (Ratio × Días) - Stock Físico.
        El cliente genera las OC manualmente, por lo que no hay riesgo de
        sobre-compra por órdenes en tránsito.

        FIX: se eliminó la condición `if rec.qty_on_hand` que era falsy cuando
        el stock era exactamente 0 y nunca ejecutaba la resta.
        """
        today = fields.Date.context_today(self)
        for rec in self:
            ratio = float(rec.ratio or 0.0)
            days = self._projection_days(rec, today=today)
            new_qty = round(ratio * days, 0) if (days > 0 and ratio) else 0.0

            # FIX: sin condición falsy — si stock = 0 también resta
            stock = rec.qty_on_hand or 0.0
            if new_qty or stock < 0:
                gap = new_qty - stock
                new_qty = gap if gap > 0.0 else 0.0

            if rec.qty_multiple and new_qty:
                new_qty = math.ceil(new_qty / rec.qty_multiple) * rec.qty_multiple

            manual_qty = float(rec.qty_to_order_manual or 0.0)
            rec.qty_to_order = manual_qty if manual_qty != 0.0 else new_qty

            rec.qty_to_order_uom = 0.0
            if rec.qty_to_order:
                if (rec.product_id.uom_id.id != rec.product_id.uom_po_id.id):
                    rec.qty_to_order_uom = round((rec.qty_to_order / rec.product_id.uom_po_id.factor_inv), 0)
                else:
                    rec.qty_to_order_uom = rec.qty_to_order

    def _inverse_qty_to_order_uom(self):
        for rec in self:
            if rec.qty_to_order_uom:
                if rec.product_id.uom_id.id != rec.product_id.uom_po_id.id:
                    rec.qty_to_order_manual = rec.qty_to_order_uom * rec.product_id.uom_po_id.factor_inv
                else:
                    rec.qty_to_order_manual = rec.qty_to_order_uom
            else:
                rec.qty_to_order_manual = 0

    def action_replenish(self, force_to_max=False):
        smart_ops = self.filtered(lambda op: op.trigger == 'smartpro')
        other_ops = self - smart_ops
        res = None
        if other_ops:
            res = super(stockWarehouseOrderpoint, other_ops).action_replenish(force_to_max=force_to_max)

        if not smart_ops:
            return res

        # Agrupar por compañia y producto para orden centralizada
        grouped = {}
        for op in smart_ops:
            key = (op.company_id, op.product_id)
            if key not in grouped:
                grouped[key] = self.env['stock.warehouse.orderpoint']
            grouped[key] |= op

        # Validar si se seleccionó 1 solo almacén en toda la acción
        selected_warehouses = smart_ops.mapped('warehouse_id')
        single_warehouse = selected_warehouses[0] if len(selected_warehouses) == 1 else False

        procurements = []
        for (company, product), ops in grouped.items():
            qty_to_order = sum(ops.mapped('qty_to_order'))
            if qty_to_order <= 0:
                continue

            if single_warehouse:
                target_warehouse = single_warehouse
            else:
                target_warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)

            if not target_warehouse:
                continue

            first_op = ops[0]
            date = first_op._get_orderpoint_procurement_date()
            values = first_op._prepare_procurement_values(date=date)
            
            # Forzar almacén destino según la regla
            values['warehouse_id'] = target_warehouse
            values['purchase_price'] = ops[0].purchase_price or ops[0].purchased_price
            # Aseguramos que pasamos el primer OP para que stock_rule lo detecte como smartpro
            values['orderpoint_id'] = first_op

            origin = ', '.join(ops.mapped('name'))
            procurements.append(self.env['procurement.group'].Procurement(
                product, qty_to_order, first_op.product_uom,
                target_warehouse.lot_stock_id, first_op.name, origin,
                company, values))

        if procurements:
            self.env['procurement.group'].with_context(from_orderpoint=True).run(procurements)

        # Recalcular cantidades (pero NO borrar qty_to_order_manual para smartpro)
        smart_ops._compute_qty_to_order()
        
        if res is not None:
            return res
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reabastecimiento'),
                'message': _('Se generó la orden de reabastecimiento correctamente.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _projection_days(self, rec, today=None):
        """Días a proyectar: desde max(hoy, date_to) hasta date_order (incluyendo extremos)."""
        today = today or fields.Date.context_today(self)
        if not rec.date_order:
            return 0
        start = max((rec.date_to or today), today)
        if rec.date_order <= start:
            return 0
        return (rec.date_order - start).days + 1

    def _get_multiple_rounded_qty(self, qty_to_order):
        _logger.warning('_get_multiple_rounded_qty-self: %s', self)
        _logger.warning('_get_multiple_rounded_qty-qty_to_order: %s', qty_to_order)
        replenishment_multiple = self.replenishment_uom_id or self._get_replenishment_multiple_alternative(qty_to_order)
        if replenishment_multiple and replenishment_multiple != self.product_id.uom_id:
            # Replace the UP by DOWN if we don't want to order more quantity than product_max_qty
            qty_to_order = self.product_id.uom_id._compute_quantity(qty_to_order, replenishment_multiple)
            qty_to_order = fields.Float.round(qty_to_order, precision_digits=0, rounding_method="UP")
            qty_to_order = replenishment_multiple._compute_quantity(qty_to_order, self.product_id.uom_id)
        _logger.warning('_get_multiple_rounded_qty-qty_to_order(R): %s', qty_to_order)
        return qty_to_order
