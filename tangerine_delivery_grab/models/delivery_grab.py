# -*- coding: utf-8 -*-
from typing import Any
from datetime import datetime, timedelta
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import ustr
from odoo.addons.tangerine_delivery_base.settings import utils
from ..settings.constants import settings
from ..api.connection import Connection
from ..api.client import Client


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
    grab_expire_token_date = fields.Datetime(string='Expire Token Date', readonly=True)

    default_grab_payer = fields.Selection(selection=settings.payer.value, string='Payer')
    default_grab_service_type = fields.Selection(selection=settings.service_type.value, string='Service Type')
    default_grab_vehicle_type = fields.Selection(selection=settings.vehicle_type.value, string='Vehicle Type')
    default_grab_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')

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

    def grab_get_access_token(self):
        try:
            self.ensure_one()
            if not self.grab_client_id:
                raise UserError(_('The field ClientID is required'))
            elif not self.grab_client_secret:
                raise UserError(_('The field Client Secret is required'))
            elif not self.grab_grant_type:
                raise UserError(_('The field Grant Type is required'))
            elif not self.grab_scope:
                raise UserError(_('The field Scope is required'))
            client = Client(Connection(self))
            route_id = utils.get_route_api(self, settings.oauth_route_code.value)
            result = client.get_access_token(route_id)
            self.write({
                'grab_token_type': result.get('token_type'),
                'access_token': result.get('access_token'),
                'grab_expire_token_date': self._compute_expires_seconds_to_datetime(result.get('expires_in'))
            })
            self._update_cron(result.get('expires_in'))
            return utils.notification('success', 'Get access token successfully')
        except Exception as e:
            raise UserError(ustr(e))

    def grab_rate_shipment(self, order):
        client = Client(Connection(self))
        route_id = utils.get_route_api(self, settings.get_quotes_route_code.value)
        result = client.get_delivery_quotes(route_id, order)
        return {
            'success': True,
            'price': result.get('quotes')[0].get('amount'),
            'error_message': False,
            'warning_message': False
        }

    def grab_send_shipping(self, pickings):
        client = Client(Connection(self))
        route_id = utils.get_route_api(self, settings.create_request_route_code.value)
        for picking in pickings:
            result = client.create_delivery_request(route_id, picking)
            return [{
                'exact_price': result.get('quote').get('amount'),
                'tracking_number': result.get('deliveryID')
            }]

    @staticmethod
    def grab_get_tracking_link(picking):
        return f'{settings.tracking_url.value}/{picking.carrier_tracking_ref}'

    def grab_cancel_shipment(self, picking):
        if picking.status_id.code in settings.list_status_cancellation_allowed.value:
            raise UserError(_(f'You cannot cancel while the order is in {picking.status_id.name} status'))
        client = Client(Connection(self))
        route_id = utils.get_route_api(self, settings.cancel_request_route_code.value)
        client.cancel_delivery(route_id, picking.carrier_tracking_ref)
        picking.write({
            'carrier_tracking_ref': False,
            'carrier_price': 0.0
        })
        return utils.notification(
            'success',
            f'Cancel tracking reference {settings.cancel_request_route_code.value} successfully'
        )

    def grab_toggle_prod_environment(self):
        self.ensure_one()
        payload = []
        for route_id in self.route_api_ids:
            item = route_id.route.split('/')
            if item[1] == settings.staging_route.value and route_id.provider_id.prod_environment:
                item[1] = settings.production_route.value
                payload.append((1, route_id.id, {'route': '/'.join(item)}))
            elif item[1] == settings.production_route.value and not route_id.provider_id.prod_environment:
                item[1] = settings.staging_route.value
                payload.append((1, route_id.id, {'route': '/'.join(item)}))
        if payload:
            self.write({'route_api_ids': payload})

    def _grab_get_default_custom_package_code(self):...

