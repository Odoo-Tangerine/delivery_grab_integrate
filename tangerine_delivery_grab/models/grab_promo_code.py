from odoo import models, fields


class GrabPromoCode(models.Model):
    _name = 'grab.promo.code'
    _description = 'Grab Promo Code'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    is_out_of_date = fields.Boolean(string='Out of Date', default=False)
    is_used = fields.Boolean(string='Used', default=False)
    is_available = fields.Boolean(string='Available', default=False)

