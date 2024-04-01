from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shipping_address_grab = fields.Char(string='Grab Shipping Address')
