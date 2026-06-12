from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    payment_lot = fields.Char('Lote del pago')
    payment_reference = fields.Char('Referencia del pago')
    payment_terminal = fields.Char('Terminal del pago')