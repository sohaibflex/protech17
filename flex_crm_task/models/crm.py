from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    activity_task_assign = fields.One2many('activity.task.assign', 'lead_activity_id', string='Activity Task')

    def create_activity_task(self):
        self.ensure_one()
        return {
            'name': 'Create Activity Task',
            'type': 'ir.actions.act_window',
            'res_model': 'task.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_lead_activity_id': self.id,
            }
        }


class ActivityTaskAssign(models.Model):
    _name = 'activity.task.assign'
    _description = 'Activity Task Assign'

    lead_activity_id = fields.Many2one('crm.lead', string='Lead')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='State', default='draft')
    task_name = fields.Char(string='Task Name')
    assigned_to = fields.Many2many('res.users', relation='activity_task_assigned_to_rel', column1='activity_task_id',
                                   column2='user_id', string='Assigned To')
    direct_manager = fields.Many2many('res.users', relation='activity_task_direct_manager_rel',
                                      column1='activity_task_id', column2='user_id', string='Direct Manager')
    deadline = fields.Date(string='Deadline')
    time_frame = fields.Many2one('time.frame', string='Time Frame')
    description = fields.Html(string='Description')

    def view_task(self):
        self.ensure_one()
        return {
            'name': 'View Task',
            'type': 'ir.actions.act_window',
            'res_model': 'view.task.details',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_activity_id': self.lead_activity_id.id,
                'default_state': self.state,
                'default_task_name': self.task_name,
                'default_assigned_to': [(6, 0, self.assigned_to.ids)],
                'default_direct_manager': [(6, 0, self.direct_manager.ids)],
                'default_deadline': self.deadline,
                'default_time_frame': self.time_frame.id,
                'default_description': self.description,
            }
        }

    def delete_line(self):
        self.unlink()

