# -*- coding: utf-8 -*-
import re
import pytz
from typing import NamedTuple, Any, Optional
from urllib.parse import urlencode, unquote_plus
from odoo import _
from odoo.exceptions import UserError
from ..settings.constants import settings


def notification(notification_type: str, message: str):
    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'type': notification_type,
            'message': _(message),
            'next': {'type': 'ir.actions.act_window_close'},
        }
    }


def generate_client_api(self, code):
    if self.delivery_type != settings.grab_code:
        raise UserError(_(f'The provider {self.name} does not support this feature.'))
    route_id = self.grab_routes_ids.search([('code', '=', code)])
    if not route_id:
        raise UserError(_(f'Route {code} not found'))
    return route_id


def datetime_to_rfc3339(dt):
    dt = dt.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
    return dt.isoformat()


class URLBuilder(NamedTuple):
    host: str
    routes: str
    params: str

    @classmethod
    def _add_query_params(cls, param_name: str, v: Optional[dict[str, str]] = None) -> str:
        if not v: return v
        elif not isinstance(v, dict): raise TypeError(f'{param_name} must be a dict')
        return urlencode(v)

    @classmethod
    def _add_routes(cls, param_name: str, v: Optional[list[str]] = None) -> str:
        if not v: return ''
        elif not isinstance(v, list): raise TypeError(f'{param_name} must be a list')
        return ''.join(v)

    @classmethod
    def _define_host(cls, param_name: str, v: str) -> str:
        if not v: raise KeyError(f'Key {param_name} missing')
        elif not isinstance(v, str): raise TypeError(f'Key {param_name} must be a string')
        return v

    @classmethod
    def to_url(cls, instance, is_unquote: Optional[bool] = None) -> str:
        if instance.params:
            if is_unquote:
                params = re.sub(r"'", '"', unquote_plus(instance.params))
            else:
                params = re.sub(r"'", '"', instance.params)
            return f'{instance.host}{instance.routes}?{params}'
        return f'{instance.host}{instance.routes}'

    @classmethod
    def builder(
            cls,
            host: str,
            routes: Optional[list[str]] = None,
            params: Optional[dict[str, Any]] = None,
            is_unquote: Optional[bool] = None
    ) -> str:
        instance = cls(
            cls._define_host('host', host),
            cls._add_routes('routes', routes),
            cls._add_query_params('params', params)
        )
        return cls.to_url(instance, is_unquote)
