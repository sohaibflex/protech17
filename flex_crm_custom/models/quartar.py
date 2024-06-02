from odoo import api, fields, models


class Quartar(models.Model):
    _name = 'quartar'
    _description = 'Quartar'

    name = fields.Char(string='Name', translate=True)
