from odoo import models, fields
from odoo.exceptions import UserError
from ..settings import utils
from ..api.client import Client
from ..api.connection import Connection
from ..settings.constants import settings
from ..schemas.grab_schemas import MultiStopDeliveryQuotesRequest


class MultiAddShippingWizard(models.TransientModel):
    _name = 'multi.add.shipping.wizard'
    _description = 'Multi Add Shipping Wizard'

    def default_get(self, fields_list):
        values = super(MultiAddShippingWizard, self).default_get(fields_list)
        if self._context['active_model'] == 'sale.order':
            sale_ids = self.env[self._context['active_model']].browse(self._context.get('active_ids'))
            values['detail_ids'] = [(0, 0, {'sale_id': sale_id.id}) for sale_id in sale_ids]
            values['carrier_id'] = self.env.ref('tangerine_delivery_grab.tangerine_delivery_grab_provider').id
            origin_address_id = list({sale_id.warehouse_id.partner_id for sale_id in sale_ids})
            if len(origin_address_id) > 1:
                raise UserError(f'In the get multi-stop delivery quotes, There cannot be 2 delivery points.\n'
                                f'{[origin.shipping_address_grab for origin in origin_address_id]}')
            elif not origin_address_id:
                raise UserError('No delivery address available')
            values['origin_address_id'] = origin_address_id[0].id
        return values

    carrier_id = fields.Many2one('delivery.carrier', readonly=True, string='Provider')
    origin_address_id = fields.Many2one('res.partner', string='Origin')
    service_type = fields.Char(string='Service Type', default='MULTI_STOP', readonly=True)
    detail_ids = fields.One2many('multi.add.shipping.line.wizard', 'header_id')

    def _prepare_payload_get_multi_stop_delivery_quotes(self):
        payload = {
            'origin': [{
                'address': self.origin_address_id.shipping_address_grab,
            }],
            'destination': [{
                'address': line_id.sale_id.partner_id.shipping_address_grab,
                'packages': [{
                    'name': line.product_id.name,
                    'description': line.name,
                    'quantity': line.product_uom_qty,
                    'price': line.price_subtotal,
                    'dimensions': {
                        'height': 0,
                        'width': 0,
                        'depth': 0,
                        'weight': line.product_id.weight
                    }
                } for line in line_id.sale_id.order_line if not line.is_delivery and not line.is_service]
            } for line_id in self.detail_ids]
        }
        return MultiStopDeliveryQuotesRequest(**payload)

    def action_get_multi_stop_delivery_quotes(self):
        client = Client(Connection(self))
        route_id = utils.generate_client_api(self.carrier_id, settings.get_multi_quotes_route_code)
        result = client.get_multi_stop_delivery_quotes(
            self.carrier_id, route_id, self._prepare_payload_get_multi_stop_delivery_quotes()
        )
        print(result)


class MultiAddShippingLineWizard(models.TransientModel):
    _name = 'multi.add.shipping.line.wizard'
    _description = 'Multi Add Shipping Line Wizard'

    header_id = fields.Many2one('multi.add.shipping.wizard')
    sale_id = fields.Many2one('sale.order')
    partner_id = fields.Many2one(related='sale_id.partner_id')
    date_order = fields.Datetime(related='sale_id.date_order')
    currency_id = fields.Many2one(related='sale_id.currency_id')
    estimate_cost = fields.Monetary(string='Cost', currency_field='currency_id')