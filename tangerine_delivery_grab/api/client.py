# -*- coding: utf-8 -*-
from typing import Any
from dataclasses import dataclass
from .connection import Connection
from ..settings.utils import URLBuilder
from ..settings.status import status
from ..schemas.grab_schemas import (
    TokenRequest, TokenResponse,
    DeliveryQuotesRequest, DeliveryQuotesResponse,
    CreateDeliveryRequest, CreateDeliveryResponse,
    MultiStopDeliveryQuotesRequest, MultiStopDeliveryQuotesResponse
)


@dataclass
class Client:
    conn: Connection

    @staticmethod
    def _build_header(provider=None) -> dict[str, str]:
        headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
        if provider:
            headers.update({'Authorization': f'{provider.grab_token_type} {provider.grab_access_token}'})
        return headers

    def get_access_token(self, provider_id, route_id, payload: TokenRequest) -> TokenResponse:
        return TokenResponse(**self.conn.execute_restful(
            url=URLBuilder.builder(
                host=provider_id.grab_host,
                routes=[route_id.route, route_id.sub_route]
            ),
            headers=self._build_header(),
            method=route_id.method,
            **payload.model_dump(exclude_none=True)
        ))

    def get_delivery_quotes(self, provider_id, route_id, payload: DeliveryQuotesRequest) -> DeliveryQuotesResponse:
        return DeliveryQuotesResponse(**self.conn.execute_restful(
            url=URLBuilder.builder(
                host=provider_id.grab_host,
                routes=[route_id.route, route_id.sub_route]
            ),
            headers=self._build_header(provider=provider_id),
            method=route_id.method,
            **payload.model_dump(exclude_none=True)
        ))

    def get_multi_stop_delivery_quotes(
            self,
            provider_id,
            route_id,
            payload: MultiStopDeliveryQuotesRequest
    ) -> MultiStopDeliveryQuotesResponse:
        return MultiStopDeliveryQuotesResponse(**self.conn.execute_restful(
            url=URLBuilder.builder(
                host=provider_id.grab_host,
                routes=[route_id.route, route_id.sub_route]
            ),
            headers=self._build_header(provider=provider_id),
            method=route_id.method,
            **payload.model_dump(exclude_none=True)
        ))

    def create_delivery_request(self, provider_id, route_id, payload: CreateDeliveryRequest) -> CreateDeliveryResponse:
        return CreateDeliveryResponse(**self.conn.execute_restful(
            url=URLBuilder.builder(
                host=provider_id.grab_host,
                routes=[route_id.route, route_id.sub_route]
            ),
            headers=self._build_header(provider=provider_id),
            method=route_id.method,
            **payload.model_dump(exclude_none=True)
        ))

    def cancel_delivery(self, provider_id, route_id, carrier_tracking_ref: str):
        self.conn.execute_restful(
            url=f'''{URLBuilder.builder(
                host=provider_id.grab_host,
                routes=[route_id.route, route_id.sub_route]
            )}/{carrier_tracking_ref}''',
            headers=self._build_header(provider=provider_id),
            method=route_id.method
        )

    def submit_tip(self, provider_id, route_id, payload: dict[str, Any]):
        return CreateDeliveryResponse(**self.conn.execute_restful(
            url=URLBuilder.builder(
                host=provider_id.grab_host,
                routes=[route_id.route, route_id.sub_route]
            ),
            headers=self._build_header(provider=provider_id),
            method=route_id.method,
            **payload
        ))