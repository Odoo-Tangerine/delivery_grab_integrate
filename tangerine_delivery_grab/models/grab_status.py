from odoo import models, fields


class GrabStatus(models.Model):
    _name = 'grab.status'
    _description = 'Grab Status'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    description = fields.Char(string='Description')

    _sql_constraints = [
        ('grab_code_uniq', 'unique(code)', 'Grab status code must be unique.'),
    ]
