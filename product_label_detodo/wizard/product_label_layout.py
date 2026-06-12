import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict
import logging
import base64
from odoo.modules import get_module_resource
import os

_logger = logging.getLogger(__name__)


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(
        selection_add=[
            ('dymo_priceless', 'Dymo sin precio'),
            ('dymo_tariffs', 'Dymo con Precio')
        ],
        ondelete={
            'dymo_priceless': 'set default',
            'dymo_tariffs': 'set default'
        }
    )

    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()
        if self.print_format == 'dymo_priceless':
            xml_id = 'product_label_detodo.dymo_label_report_priceless'
            # data['zpl_template'] = self.zpl_template
        elif self.print_format == 'dymo_tariffs':
            xml_id = 'product_label_detodo.dymo_label_report_all_tariffs'
        elif self.print_format == 'dymo':
            xml_id = 'product_label_detodo.action_report_dymo_override'

        return xml_id, data


class ProductLabelReportDymoPriceless(models.AbstractModel):
    _name = 'report.product_label_detodo.dymo_label_template_priceless'
    _description = 'Product Label Report for Dymo Priceless'

    def _get_report_values(self, docids, data):
        res = _prepare_data(self.env, docids, data)
        return res


def _prepare_data(env, docids, data):
    # change product ids by actual product object to get access to fields in xml template
    # we needed to pass ids because reports only accepts native python types (int, float, strings, ...)

    layout_wizard = env['product.label.layout'].browse(data.get('layout_wizard'))
    if data.get('active_model') == 'product.template':
        Product = env['product.template'].with_context(display_default_code=False)
    elif data.get('active_model') == 'product.product':
        Product = env['product.product'].with_context(display_default_code=False)
    elif data.get("studio") and docids:
        # special case: users trying to customize labels
        products = env['product.template'].with_context(display_default_code=False).browse(docids)
        quantity_by_product = defaultdict(list)
        for product in products:
            quantity_by_product[product].append((product.barcode, 1))
        return {
            'quantity': quantity_by_product,
            'page_numbers': 1,
            'pricelist': layout_wizard.pricelist_id,
        }
    else:
        raise UserError(_('Product model not defined, Please contact your administrator.'))

    if not layout_wizard:
        return {}

    total = 0
    qty_by_product_in = data.get('quantity_by_product')
    # search for products all at once, ordered by name desc since popitem() used in xml to print the labels
    # is LIFO, which results in ordering by product name in the report
    products = Product.search([('id', 'in', [int(p) for p in qty_by_product_in.keys()])], order='name desc')
    quantity_by_product = defaultdict(list)
    for product in products:
        q = qty_by_product_in[str(product.id)]
        quantity_by_product[product].append((product.barcode, q))
        total += q
    if data.get('custom_barcodes'):
        # we expect custom barcodes format as: {product: [(barcode, qty_of_barcode)]}
        for product, barcodes_qtys in data.get('custom_barcodes').items():
            quantity_by_product[Product.browse(int(product))] += (barcodes_qtys)
            total += sum(qty for _, qty in barcodes_qtys)

    return {
        'quantity': quantity_by_product,
        'page_numbers': (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1,
        'price_included': data.get('price_included'),
        'extra_html': layout_wizard.extra_html,
        'pricelist': layout_wizard.pricelist_id,
    }


# Reemplazo de Metodo (Dymo)
class ProductLabelReportDymoOverride(models.AbstractModel):
    _name = 'report.product_label_detodo.dymo_override_template'
    _description = 'Product Label Report Dymo Override'

    def _get_report_values(self, docids, data):
        return _prepare_all_tariffs_data(self.env, docids, data)


class ProductLabelReportAllTariffs(models.AbstractModel):
    # El nombre de este modelo DEBE coincidir con el 'xml_id' que definiste arriba.
    # El formato es 'report.nombre_modulo.id_template_xml' [2].
    _name = 'report.product_label_detodo.dymo_label_template_all_tariffs'
    _description = 'Product Label Report with All Tariffs'

    def _get_report_values(self, docids, data):
        # Este método llama a una nueva función para preparar los datos específicos
        # que necesita nuestra etiqueta de "All Tarifas".
        return _prepare_all_tariffs_data(self.env, docids, data)



def _get_logo_base64(env):
    """
    Lee la imagen del logo desde la ruta estática del módulo y la convierte a Base64.
    Esto garantiza que wkhtmltopdf pueda renderizarla.
    """
    logo_path = get_module_resource('product_label_detodo', 'static/src/img', 'logo.png')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as logo_file:
            logo_data = logo_file.read()
            logo_base64 = base64.b64encode(logo_data)
            return logo_base64.decode('utf-8')
    return None


def _prepare_all_tariffs_data(env, docids, data):
    """
    Esta función recopila los productos y, para cada uno, busca su precio
    en todas las listas de precios activas.
    """
    # Se reutiliza la lógica original para obtener el asistente y el modelo de producto [3].
    layout_wizard = env['product.label.layout'].browse(data.get('layout_wizard'))
    if data.get('active_model') == 'product.template':
        Product = env['product.template'].with_context(display_default_code=False)
    elif data.get('active_model') == 'product.product':
        Product = env['product.product'].with_context(display_default_code=False)
    else:
        # Se podría añadir manejo para casos especiales como Studio, similar al original [4].
        raise UserError(_('Product model not defined, Please contact your administrator.'))

    qty_by_product_in = data.get('quantity_by_product')

    # Producto
    products = Product.search([('id', 'in',
                                [int(p) for p in qty_by_product_in.keys()])], order='name desc')

    product_report = []
    for product in products:
        qty_by_product = qty_by_product_in[str(product.id)]
        if hasattr(product, 'list_price_total'):  # Si posee el modulo
            price = product.list_price_total
        else:
            price = product.list_price

        price_second_tariff = product.list_secondary_price_total

        current_dict_template = {
            'description': product.name,
            'price': price,
            'price_second_tarrif': price_second_tariff,
            'ref_product': product.default_code,
            'date_imp': datetime.datetime.now().strftime('%d%b').upper(),
            'repeat_qty': qty_by_product,
            'barcode': product.barcode,
        }
        product_report.append(current_dict_template)

    # logo_base64 = _get_logo_base64(env)
    return {
        'products': product_report
    }