# -*- coding: utf-8 -*-
from uuid import uuid4
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    grab_api_key = fields.Char(string='API Key')
    grab_auto_confirm_po = fields.Boolean(string='Automatically Confirm Purchase Order')
    grab_auto_create_bill = fields.Boolean(string='Automatically Create Bill')
    grab_auto_confirm_bill = fields.Boolean(string='Automatically Confirm Bill')
    grab_auto_register_payment = fields.Boolean(string='Automatically Register Payment')
    module_delivery_grab = fields.Boolean('Grab Connector')

    def grab_generate_api_key(self):
        ICPModel = self.env['ir.config_parameter'].sudo()
        ICPModel.set_param('tangerine_delivery_grab.grab_api_key', uuid4())

    def set_values(self):
        super().set_values()
        ICPModel = self.env['ir.config_parameter'].sudo()
        ICPModel.set_param('tangerine_delivery_grab.grab_api_key', self.grab_api_key)
        ICPModel.set_param('tangerine_delivery_grab.grab_auto_confirm_po', self.grab_auto_confirm_po)
        ICPModel.set_param('tangerine_delivery_grab.grab_auto_create_bill', self.grab_auto_create_bill)
        ICPModel.set_param('tangerine_delivery_grab.grab_auto_confirm_bill', self.grab_auto_confirm_bill)
        ICPModel.set_param('tangerine_delivery_grab.grab_auto_register_payment', self.grab_auto_register_payment)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPModel = self.env['ir.config_parameter'].sudo()
        res.update(
            grab_api_key=ICPModel.get_param('tangerine_delivery_grab.grab_api_key'),
            grab_auto_confirm_po=ICPModel.get_param('tangerine_delivery_grab.grab_auto_confirm_po'),
            grab_auto_create_bill=ICPModel.get_param('tangerine_delivery_grab.grab_auto_create_bill'),
            grab_auto_confirm_bill=ICPModel.get_param('tangerine_delivery_grab.grab_auto_confirm_bill'),
            grab_auto_register_payment=ICPModel.get_param('tangerine_delivery_grab.grab_auto_register_payment'),
        )
        return res
