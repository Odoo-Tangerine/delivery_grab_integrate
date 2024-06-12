# -*- coding: utf-8 -*-
import json
import math
from dataclasses import dataclass
from odoo import _
from odoo.tools.safe_eval import safe_eval
from odoo.addons.tangerine_delivery_base.settings.utils import (
    URLBuilder,
    datetime_to_rfc3339,
    standardization_e164
)
from odoo.exceptions import UserError
from .connection import Connection


@dataclass
class Client:
    conn: Connection

    def _build_header(self, route_id):
        headers = json.loads(safe_eval(route_id.headers))
        if route_id.is_need_access_token:
            headers.update({'Authorization': f'{self.conn.provider.grab_token_type} {self.conn.provider.access_token}'})
        return headers

    def _payload_get_token(self):
        return {
            'client_id': self.conn.provider.grab_client_id,
            'client_secret': self.conn.provider.grab_client_secret,
            'grant_type': self.conn.provider.grab_grant_type,
            'scope': self.conn.provider.grab_scope
        }

    def _execute(self, route_id, payload):
        return self.conn.execute_restful(
            url=URLBuilder.builder(
                host=self.conn.provider.domain,
                routes=[route_id.route]
            ),
            headers=self._build_header(route_id),
            method=route_id.method,
            **payload or {}
        )

    def get_access_token(self, route_id):
        return self._execute(route_id, self._payload_get_token())

    def _payload_delivery_quotes(self, order):
        payload = {
            'origin': {
                'address': f'{order.warehouse_id.partner_id.shipping_address}',
                'coordinates': {}
            },
            'destination': {
                'address': f'{order.partner_shipping_id.shipping_address}',
                'coordinates': {}
            },
            'packages': [{
                'name': line.product_id.name,
                'description': line.name,
                'quantity': int(line.product_uom_qty),
                'price': int(line.price_subtotal),
                'dimensions': {
                    'height': 0,
                    'width': 0,
                    'depth': 0,
                    'weight': math.ceil(self.conn.provider.convert_weight(
                        line.product_id.weight,
                        self.conn.provider.base_weight_unit
                    ))
                }
            } for line in order.order_line if not line.is_delivery and not line.is_service]
        }
        if order.env.context.get('grab_service_type'):
            payload.update({'serviceType': order.env.context.get('grab_service_type')})
        if order.env.context.get('grab_vehicle_type'):
            payload.update({'vehicleType': order.env.context.get('grab_vehicle_type')})
        return payload

    def get_delivery_quotes(self, route_id, order):
        return self._execute(route_id, self._payload_delivery_quotes(order))

    @staticmethod
    def _validate_picking(picking):
        if not picking.partner_id.phone and not picking.partner_id.mobile:
            raise UserError(_('The number phone of recipient is required.'))
        if picking.promo_code and not picking.grab_payment_method:
            raise UserError(_('You are using a promo code, please select a payment method. This is required.'))
        elif picking.grab_payer == 'RECIPIENT' and picking.grab_payment_method == 'CASHLESS':
            raise UserError(_('Sending a RECIPIENT value for CASHLESS payments will result in an error.'))
        elif picking.cash_on_delivery and picking.cash_on_delivery_amount <= 0.0:
            raise UserError(_('The cash on delivery amount must be greater than 0.'))
        elif picking.schedule_order and not picking.schedule_pickup_time_from:
            raise UserError(_('You are using Scheduled for Order. Please select the pickup time from.'))
        elif picking.schedule_order and not picking.schedule_pickup_time_to:
            raise UserError(_('You are using Scheduled for Order. Please select the pickup time to.'))
        elif picking.schedule_order and (picking.schedule_pickup_time_from >= picking.schedule_pickup_time_to):
            raise UserError(_('The delivery time in the future must be greater than the present time.'))

    def _payload_create_delivery_request(self, picking):
        self._validate_picking(picking)
        payload = {
            'merchantOrderID': picking.origin,
            'serviceType': picking.grab_service_type,
            'vehicleType': picking.grab_vehicle_type,
            'codType': picking.grab_cod_type,
            'paymentMethod': picking.grab_payment_method,
            'payer': picking.grab_payer,
            'highValue': picking.grab_high_value,
            'packages': [{
                'name': line.product_id.name,
                'description': line.product_id.name,
                'quantity': int(line.quantity),
                'dimensions': {
                    'height': 0,
                    'width': 0,
                    'depth': 0,
                    'weight': math.ceil(self.conn.provider.convert_weight(
                        line.product_id.weight,
                        self.conn.provider.base_weight_unit
                    ))
                }
            } for line in picking.move_ids],
            'sender': {
                'firstName': picking.picking_type_id.warehouse_id.partner_id.name,
                'email': picking.picking_type_id.warehouse_id.partner_id.email or '',
                'phone': standardization_e164(picking.picking_type_id.warehouse_id.partner_id.phone)
            },
            'recipient': {
                'firstName': picking.partner_id.name,
                'email': picking.partner_id.email or '',
                'phone': standardization_e164(picking.partner_id.phone)
            },
            'origin': {
                'address': picking.picking_type_id.warehouse_id.partner_id.shipping_address,
                'coordinates': {}
            },
            'destination': {
                'address': picking.partner_id.shipping_address,
                'coordinates': {}
            }
        }
        if picking.cash_on_delivery:
            payload.update({'cashOnDelivery': {'amount': picking.cash_on_delivery_amount}})
        if picking.schedule_order:
            payload.update({
                'schedule': {
                    'pickupTimeFrom': datetime_to_rfc3339(picking.schedule_pickup_time_from, picking.env.user.tz),
                    'pickupTimeTo': datetime_to_rfc3339(picking.schedule_pickup_time_to, picking.env.user.tz)
                }
            })
        return payload

    def create_delivery_request(self, route_id, picking):
        return self._execute(route_id, self._payload_create_delivery_request(picking))

    def cancel_delivery(self, route_id, carrier_tracking_ref: str):
        self.conn.execute_restful(
            url=f'''{URLBuilder.builder(
                host=self.conn.provider.domain,
                routes=[route_id.route]
            )}/{carrier_tracking_ref}''',
            headers=self._build_header(route_id),
            method=route_id.method
        )
