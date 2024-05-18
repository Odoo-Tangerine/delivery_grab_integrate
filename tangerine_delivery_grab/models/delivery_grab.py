# -*- coding: utf-8 -*-
import requests
from typing import Any
from datetime import datetime, timedelta
from requests.exceptions import ConnectionError, ConnectTimeout
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import ustr
from ..settings import utils
from ..settings.constants import settings
from ..api.connection import Connection
from ..api.client import Client

from ..schemas.grab_schemas import (
    TokenRequest,
    DeliveryQuotesRequest,
    CreateDeliveryRequest
)


class ProviderGrab(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('grab', 'Grab Express')
    ], ondelete={'grab': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    grab_partner_id = fields.Char(string='PartnerID')
    grab_client_id = fields.Char(string='ClientID')
    grab_client_secret = fields.Char(string='Client Secret')
    grab_grant_type = fields.Char(string='Grant Type')
    grab_scope = fields.Char(string='Scope')
    grab_token_type = fields.Char(string='Token Type')
    grab_access_token = fields.Char(string='Access Token')
    grab_host = fields.Char(string='Grab Host')
    grab_expire_token_date = fields.Datetime(string='Expire Token Date', readonly=True)
    grab_routes_ids = fields.One2many('grab.routes.api', 'provider_id', string='Endpoints')

    def grab_action_test_connection(self):
        self.ensure_one()
        try:
            requests.get(self.grab_host, timeout=3)
            return utils.notification(settings.notice_success_type, 'Test connection successfully')
        except ConnectTimeout:
            return utils.notification(settings.notice_danger_type, 'Test connection timeout')
        except ConnectionError:
            return utils.notification(settings.notice_danger_type, 'Test connection error')

    def _payload_oauth_grab(self):
        if not self.grab_client_id:
            raise UserError(_('The field ClientID is required'))
        elif not self.grab_client_secret:
            raise UserError(_('The field Client Secret is required'))
        elif not self.grab_grant_type:
            raise UserError(_('The field Grant Type is required'))
        elif not self.grab_scope:
            raise UserError(_('The field Scope is required'))
        return {
            'client_id': self.grab_client_id,
            'client_secret': self.grab_client_secret,
            'grant_type': self.grab_grant_type,
            'scope': self.grab_scope
        }

    def _update_cron(self, expires_times):
        cron = self.env.ref('tangerine_delivery_grab.ir_cron_refresh_access_token_grab', raise_if_not_found=False)
        if cron:
            cron.try_write({
                'nextcall': datetime.now() + timedelta(seconds=expires_times),
                'active': True
            })

    @staticmethod
    def _compute_expires_seconds_to_datetime(expires_times):
        return datetime.now() + timedelta(seconds=expires_times)

    def _payload_get_token(self) -> TokenRequest:
        return TokenRequest(
            client_id=self.grab_client_id,
            client_secret=self.grab_client_secret,
            grant_type=self.grab_grant_type,
            scope=self.grab_scope
        )

    def grab_get_access_token(self):
        try:
            client = Client(Connection(self))
            route_id = utils.generate_client_api(self, settings.oauth_route_code)
            result = client.get_access_token(self, route_id, self._payload_get_token())
            self.write({
                'grab_token_type': result.token_type,
                'grab_access_token': result.access_token,
                'grab_expire_token_date': self._compute_expires_seconds_to_datetime(result.expires_in)
            })
            self._update_cron(result.expires_in)
            return utils.notification(settings.notice_success_type, 'Get access token successfully')
        except Exception as e:
            raise UserError(ustr(e))

    def _payload_delivery_quotes(self, order) -> DeliveryQuotesRequest:
        payload = {
            'origin': {
                'address': f'{order.warehouse_id.partner_id.shipping_address_grab}'
            },
            'destination': {
                'address': f'{order.partner_shipping_id.shipping_address_grab}'
            },
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
            } for line in order.order_line if not line.is_delivery and not line.is_service]
        }
        if self.env.context.get('grab_service_type'):
            payload.update({'serviceType': self.env.context.get('grab_service_type')})
        if self.env.context.get('grab_vehicle_type'):
            payload.update({'vehicleType': self.env.context.get('grab_vehicle_type')})
        return DeliveryQuotesRequest(**payload)

    def grab_rate_shipment(self, order) -> dict[str, Any]:
        client = Client(Connection(self))
        route_id = utils.generate_client_api(self, settings.get_quotes_route_code)
        result = client.get_delivery_quotes(self, route_id, self._payload_delivery_quotes(order))
        return {
            'success': True,
            'price': result.quotes[0].amount,
            'error_message': False,
            'warning_message': False
        }

    @staticmethod
    def _validate_picking(picking):
        if not picking.partner_id.phone and not picking.partner_id.mobile:
            raise UserError(_('The number phone of recipient is required.'))
        if picking.grab_promo_code and not picking.grab_payment_method:
            raise UserError(_('You are using a promo code, please select a payment method. This is required.'))
        # elif picking.grab_payer == 'RECIPIENT' and picking.grab_payment_method == 'CASHLESS':
        #     raise UserError(_('Sending a RECIPIENT value for CASHLESS payments will result in an error.'))
        elif picking.grab_cash_on_delivery and picking.grab_cash_on_delivery_amount <= 0.0:
            raise UserError(_('The cash on delivery amount must be greater than 0.'))
        elif picking.grab_schedule_order and not picking.grab_schedule_pickup_time_from:
            raise UserError(_('You are using Scheduled for Order. Please select the pickup time from.'))
        elif picking.grab_schedule_order and not picking.grab_schedule_pickup_time_to:
            raise UserError(_('You are using Scheduled for Order. Please select the pickup time to.'))
        elif picking.grab_schedule_order and (
                picking.grab_schedule_pickup_time_from >= picking.grab_schedule_pickup_time_to
        ):
            raise UserError(_('The delivery time in the future must be greater than the present time.'))

    @staticmethod
    def _clean_up_phone_number(phone_number: str) -> str:
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        return phone_number

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
                'quantity': line.quantity,
                'dimensions': {
                    'height': 0,
                    'width': 0,
                    'depth': 0,
                    'weight': line.product_id.weight
                }
            } for line in picking.move_ids],
            'sender': {
                'firstName': picking.picking_type_id.warehouse_id.partner_id.name,
                'email': picking.picking_type_id.warehouse_id.partner_id.email or None,
                'phone': self._clean_up_phone_number(picking.picking_type_id.warehouse_id.partner_id.phone)
            },
            'recipient': {
                'firstName': picking.partner_id.name,
                'email': picking.partner_id.email or None,
                'phone': self._clean_up_phone_number(picking.partner_id.phone)
            },
            'origin': {
                'address': picking.picking_type_id.warehouse_id.partner_id.shipping_address_grab
            },
            'destination': {
                'address': picking.partner_id.shipping_address_grab
            }
        }
        if picking.grab_cash_on_delivery:
            payload.update({'cashOnDelivery': {'amount': picking.grab_cash_on_delivery_amount}})
        if picking.grab_schedule_order:
            payload.update({
                'schedule': {
                    'pickupTimeFrom': utils.datetime_to_rfc3339(
                        picking.grab_schedule_pickup_time_from, self.env.user.tz
                    ),
                    'pickupTimeTo': utils.datetime_to_rfc3339(
                        picking.grab_schedule_pickup_time_to,
                        self.env.user.tz
                    )
                }
            })
        return CreateDeliveryRequest(**payload)

    def grab_send_shipping(self, pickings):
        client = Client(Connection(self))
        route_id = utils.generate_client_api(self, settings.create_request_route_code)
        for picking in pickings:
            result = client.create_delivery_request(self, route_id, self._payload_create_delivery_request(picking))
            self.env['grab.delivery.order'].sudo().create({'picking_id': picking.id})
            return [{
                'exact_price': result.quote.amount,
                'tracking_number': result.deliveryID
            }]

    @staticmethod
    def grab_get_tracking_link(picking):
        return f'{settings.tracking_url}/{picking.carrier_tracking_ref}'

    def grab_cancel_shipment(self, picking):
        if picking.grab_status_id.code in settings.list_status_cancellation_allowed:
            raise UserError(_(f'You cannot cancel while the order is in {picking.grab_status_id.name} status'))
        client = Client(Connection(self))
        route_id = utils.generate_client_api(self, settings.cancel_request_route_code)
        client.cancel_delivery(self, route_id, picking.carrier_tracking_ref)
        picking.write({
            'carrier_tracking_ref': False,
            'carrier_price': 0.0
        })
        return utils.notification(
            settings.notice_success_type,
            f'Cancel tracking reference {settings.cancel_request_route_code} successfully'
        )

    def _grab_get_default_custom_package_code(self):...

