# -*- coding: utf-8 -*-
from odoo import models, fields


class GrabRoutesAPI(models.Model):
    _name = 'grab.routes.api'
    _inherit = ['mail.thread']
    _description = 'Grab Endpoints API'

    provider_id = fields.Many2one('delivery.carrier', string='Provider', required=True)
    name = fields.Char(string='Name', tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True, index=True)
    route = fields.Char(string='Route', required=True, tracking=True)
    sub_route = fields.Char(string='Sub-Route', required=True, tracking=True)
    description = fields.Text(string='Description')
    method = fields.Selection([
        ('POST', 'POST'),
        ('DELETE', 'DELETE'),
        ('PUT', 'PUT'),
        ('GET', 'GET')
    ], string='Method', required=True, tracking=True)
    active = fields.Boolean(default=True)
