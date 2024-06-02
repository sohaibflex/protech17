from odoo import api, fields, models


class ProductAssign(models.TransientModel):
    _name = 'bum.division.assign'
    _description = 'Assign Bid Team'

    lead_id = fields.Many2one('crm.lead', string='Lead', default=lambda self: self._context.get('active_id'))

    bdm_manager = fields.Many2many('division.manager', string='Business Division Manager')

    def confirm_assign(self):
        for rec in self:
            if rec.env.user.notification_type == 'email':
                rec.env['mail.mail'].sudo().create({
                    'subject': 'Lead Name:' + " " + rec.lead_id.name,
                    'email_from': rec.env.user.email,
                    'email_to': rec.bdm_manager.mapped('email'),
                    'body_html': f'</p><p>Need To Convert To Opportunity</p><p>Lead Name: {rec.lead_id.name}</p><p>Lead ID: {rec.lead_id.id}</p>',
                }).send()
            elif rec.env.user.notification_type == 'inbox':
                # add it for activity
                rec.env['mail.activity'].sudo().create({
                    'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                    'note': 'Need To Convert To Opportunity',
                    'res_id': rec.lead_id.id,
                    'res_model_id': rec.env.ref('crm.model_crm_lead').id,
                    'user_id': rec.user_ids.id,
                })

        # make email for assigned team

        return {'type': 'ir.actions.act_window_close'}

    def cancel_assign(self):
        lead_id = self.env['crm.lead'].browse(self._context.get('active_id'))
        for rec in lead_id:
            rec.state = 'sale_account_manager'
        return {'type': 'ir.actions.act_window_close'}
