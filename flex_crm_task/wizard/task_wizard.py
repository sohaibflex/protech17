from odoo import api, fields, models


class TaskWizard(models.TransientModel):
    _name = 'task.wizard'
    _description = 'Task Wizard'
    _rec_name = 'task_name'

    lead_id = fields.Many2one('crm.lead', string='Lead', default=lambda self: self._context.get('active_id'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='State', default='draft')
    task_name = fields.Char(string='Activity Name', required=True)
    assigned_to = fields.Many2many('res.users', relation='task_wizard_assigned_to_rel', column1='task_wizard_id',
                                   column2='lead_id', string='Assigned To')
    direct_manager = fields.Many2many('res.users', relation='task_wizard_direct_manager_rel', column1='task_wizard_id',
                                      column2='lead_id', string='Direct Manager',
                                      compute='_compute_direct_manager', store=True)
    deadline = fields.Date(string='Deadline')
    time_frame = fields.Many2one('time.frame', string='Time Frame')
    description = fields.Html(string='Description')

    @api.depends('assigned_to')
    def _compute_direct_manager(self):
        for rec in self:
            if rec.assigned_to:
                rec.direct_manager = rec.assigned_to.mapped('direct_manager_id')
            else:
                rec.direct_manager = False

    def create_activity_task(self):
        activity_task_assign = self.env['activity.task.assign']
        for rec in self:
            users = rec.assigned_to
            cc_users = rec.direct_manager
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            # make url to this task crm.lead
            crm_lead_id = self.env['crm.lead'].search([('id', '=', rec.lead_id.id)])
            url = f'{base_url}/web#id={crm_lead_id.id}&view_type=form&model=crm.lead'
            email_body = f'<p>Dear Team,</p><p>This Task has been Assigned:</p><p>Task Name: {rec.task_name}</p><p>Deadline: {rec.deadline}</p><p>Time Frame: {rec.time_frame.name}</p><p>Opportunity Url: <a href="{url}">Click Here</a></p>'

            for user in users:
                if user.notification_type == 'email':
                    self.env['mail.mail'].sudo().create({
                        'subject': 'Task Assigned',
                        'email_from': self.env.user.email,
                        'email_to': ','.join(map(str, user.mapped('email'))),
                        'email_cc': ','.join(map(str, cc_users.mapped('email'))),
                        'body_html': email_body,
                    }).send()
                elif user.notification_type == 'inbox':
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'note': 'Task Assigned',
                        'res_id': rec.id,
                        'res_model_id': self.env.ref('flex_crm_task.model_task_wizard').id,
                        'user_id': user.id,
                    })

        activity_task_assign.create({
            'lead_activity_id': self.lead_id.id,
            'task_name': self.task_name,
            'assigned_to': [(6, 0, self.assigned_to.ids)],
            'direct_manager': [(6, 0, self.direct_manager.ids)],
            'deadline': self.deadline,
            'time_frame': self.time_frame.id,
            'description': self.description,
            'state': self.state
        })
        return {
            'type': 'ir.actions.act_window_close'
        }

    def cancel_activity_task(self):
        lead_id = self.env['crm.lead'].browse(self._context.get('active_id'))
        for rec in lead_id:
            rec.task_name = 'sale_account_manager'
        return {'type': 'ir.actions.act_window_close', 'res_id': lead_id.id}


class ViewTaskWizard(models.TransientModel):
    _name = 'view.task.wizard'
    _description = 'View Task Wizard'
    _rec_name = 'task_name'

    activity_id = fields.Many2one('activity.task.assign', default=lambda self: self._context.get('active_id'))
    task_name = fields.Char(string='Activity Name', required=True)
    assigned_to = fields.Many2many('res.users', relation='view_task_wizard_assigned_to_rel',
                                   column1='view_task_wizard_id',
                                   column2='activity_id', string='Assigned To')
    direct_manager = fields.Many2many('res.users', relation='view_task_wizard_direct_manager_rel',
                                      column1='view_task_wizard_id',
                                      column2='activity_id', string='Direct Manager')
    deadline = fields.Date(string='Deadline')
    time_frame = fields.Many2one('time.frame', string='Time Frame')
    description = fields.Html(string='Description')


class TimeFrame(models.Model):
    _name = 'time.frame'
    _description = 'Time Frame'

    name = fields.Char(string='Name')


class ViewTaskDetails(models.TransientModel):
    _name = 'view.task.details'
    _description = 'View Task Details'
    _rec_name = 'task_name'

    # activity_task_assign = fields.Many2one('activity.task.assign', default=lambda self: self._context.get('active_id'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='State', default='draft')
    activity_id = fields.Many2one('activity.task.assign', default=lambda self: self._context.get('active_id'))
    task_name = fields.Char(string='Activity Name', required=True)
    assigned_to = fields.Many2many('res.users', relation='view_task_details_assigned_to_rel',
                                   column1='view_task_details_id',
                                   column2='activity_id', string='Assigned To')
    direct_manager = fields.Many2many('res.users', relation='view_task_details_direct_manager_rel',
                                      column1='view_task_details_id',
                                      column2='activity_id', string='Direct Manager')
    deadline = fields.Date(string='Deadline')
    time_frame = fields.Many2one('time.frame', string='Time Frame')
    description = fields.Html(string='Description')

    def save_details(self):
        self.ensure_one()
        self.activity_id.write({
            'state': self.state,
            'task_name': self.task_name,
            'assigned_to': [(6, 0, self.assigned_to.ids)],
            'direct_manager': [(6, 0, self.direct_manager.ids)],
            'deadline': self.deadline,
            'time_frame': self.time_frame.id,
            'description': self.description,
        })
        # if state is done then send email to assigned_to users and direct_manager users in cc thats is done
        if self.state == 'done':
            users = self.assigned_to
            cc_users = self.direct_manager
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            # make url to this task crm.lead
            crm_lead_id = self.env['crm.lead'].search([('id', '=', self.activity_id.lead_activity_id.id)])
            url = f'{base_url}/web#id={crm_lead_id.id}&view_type=form&model=crm.lead'
            email_body = f'<p>Dear Team,</p><p>This Task has been Done:</p><p>Task Name: {self.task_name}</p><p>Deadline: {self.deadline}</p><p>Time Frame: {self.time_frame.name}</p><p>Opportunity Url: <a href="{url}">Click Here</a></p>'

            for user in users:
                if user.notification_type == 'email':
                    self.env['mail.mail'].sudo().create({
                        'subject': 'Task Done',
                        'email_from': self.env.user.email,
                        'email_to': ','.join(map(str, user.mapped('email'))),
                        'email_cc': ','.join(map(str, cc_users.mapped('email'))),
                        'body_html': email_body,
                    }).send()
                elif user.notification_type == 'inbox':
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'note': 'Task Done',
                        'res_id': self.activity_id.id,
                        'res_model_id': self.env.ref('flex_crm_task.model_activity_task_assign').id,
                        'user_id': user.id,
                    })
