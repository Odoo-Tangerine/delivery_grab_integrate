from odoo import fields, models


class GrabDeliveryOrder(models.Model):
    _name = 'grab.delivery.order'
    _rec_name = 'delivery_id'
    _description = 'Grab Delivery Order'

    picking_id = fields.Many2one('stock.picking', string='Delivery Order')
    status_id = fields.Many2one(related='picking_id.grab_status_id')
    delivery_id = fields.Char(related='picking_id.carrier_tracking_ref')
    shipping_cost = fields.Float(related='picking_id.carrier_price')
    service_type = fields.Selection(related='picking_id.grab_service_type')
    vehicle_type = fields.Selection(related='picking_id.grab_vehicle_type')
    cod_type = fields.Selection(related='picking_id.grab_cod_type')
    payment_method = fields.Selection(related='picking_id.grab_payment_method')
    payer = fields.Selection(related='picking_id.grab_payer')
    high_value = fields.Boolean(related='picking_id.grab_high_value')
    cod_amount = fields.Float(related='picking_id.grab_cash_on_delivery_amount')
    promo_code = fields.Char(related='picking_id.grab_promo_code')
    schedule_pickup_time_from = fields.Datetime(related='picking_id.grab_schedule_pickup_time_from')
    schedule_pickup_time_to = fields.Datetime(related='picking_id.grab_schedule_pickup_time_to')
    driver_name = fields.Char(related='picking_id.grab_driver_name', string='Name')
    driver_license_plate = fields.Char(related='picking_id.grab_driver_license_plate', string='License Plate')
    driver_phone = fields.Char(related='picking_id.grab_driver_phone', string='Phone')
    driver_photo_url = fields.Char(related='picking_id.grab_driver_photo_url', string='Photo URL')
    driver_current_lat = fields.Char(related='picking_id.grab_driver_current_lat', string='Current Lat')
    driver_current_lng = fields.Char(related='picking_id.grab_driver_current_lng', string='Current Lng')
