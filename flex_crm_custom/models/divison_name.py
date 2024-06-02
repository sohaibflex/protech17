from odoo import api, fields, models


class DivisionName(models.Model):
    _name = 'division.name'
    _description = 'Division Name'
    _rec_name = 'division_name'

    division_name = fields.Char(string='Division Name', required=True, translate=True)
    business_division_manager = fields.Many2many('res.users', string='Business Division Manager', domain=lambda self: [
        ("groups_id", "=", self.env.ref("flex_crm_custom.access_bum").id)])
