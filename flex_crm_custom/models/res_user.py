from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    direct_manager_id = fields.Many2many('res.users', 'res_users_rel', 'user_id', 'manager_id', string='Direct Manager',
                                         domain=lambda self: [
                                             ("groups_id", "=", self.env.ref("flex_crm_custom.access_bum").id)])
