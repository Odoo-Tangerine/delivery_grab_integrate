from odoo.tools import ustr
from odoo.http import request, Controller, route
from odoo.addons.tangerine_delivery_base.settings.status import status
from odoo.addons.tangerine_delivery_base.settings.utils import validate_api_key, response


class DeliveriesController(Controller):

    @validate_api_key
    @route('/api/v1/webhook/grab', type='json', auth='public', methods=['POST'])
    def grab_callback(self):
        try:
            body = request.dispatcher.jsonrequest
            picking_id = request.env['stock.picking'].sudo().search([
                ('carrier_tracking_ref', '=', body.get('deliveryID'))
            ])
            if not picking_id:
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery id {body.get("deliveryID")} not found.'
                )

            status_id = request.env['delivery.status'].sudo().search([('code', '=', body.get('status'))])
            if not status_id:
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The status {body.get("status")} does not match my system.'
                )
            payload = {'status_id': status_id.id}
            if body.get('driver'):
                payload.update({
                    'driver_name': body.get('driver').get('name'),
                    'grab_driver_license_plate': body.get('driver').get('licensePlate'),
                    'driver_phone': body.get('driver').get('phone'),
                    'grab_driver_photo_url': body.get('driver').get('photoURL'),
                })
            picking_id.sudo().write(payload)
        except Exception as e:
            return response(status=status.HTTP_500_INTERNAL_SERVER_ERROR.value, message=ustr(e))
