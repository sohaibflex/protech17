from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_active_group = fields.Boolean(string='Is Active Group', default=False, compute='_compute_is_active_group')

    def _compute_is_active_group(self):
        for partner in self:
            partner.is_active_group = partner.activity_user_ids.filtered(lambda user: user.active).mapped('id')