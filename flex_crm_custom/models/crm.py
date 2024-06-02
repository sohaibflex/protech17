from datetime import datetime

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    state = fields.Selection([
        ('sale_account_manager', 'Sales Account Manager'),
        ('business_unit_manager', 'Business Division Manager'),
        ('opp', 'Opportunity'),
        ('lost', 'Lost'),
    ], string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='sale_account_manager', )

    check_active = fields.Boolean(string='Check Active', default=False)

    is_lost = fields.Boolean(string='Is Lost', default=False)

    # lead
    vendor = fields.Many2many('res.partner', 'crm_lead_vendor_rel', 'lead_id', string='Vendor')
    # oppurtinty
    value_estimate = fields.Float(string='Value Estimate', tracking=True)
    forcast = fields.Selection([
        ('draft', 'Draft'),
        ('commit', 'Commit'),
        ('not_commit', 'Not Commit'),
    ], string='Forcast', tracking=True, default='draft')
    sale_account_manager = fields.Many2many(
        'res.users',
        string='Sales Account Manager',
        domain=lambda self: [("groups_id", "=", self.env.ref("flex_crm_custom.access_sale_account_manager").id)],
    )
    bdm_manager = fields.Many2many(
        'res.users',
        'crm_lead_bdm_manager_rel',  # Explicit intermediary table name
        'lead_id',  # Column referring to this model
        'user_id',  # Column referring to the target model
        string='Business Division Manager',
        related='division.business_division_manager',
    )
    product_manager = fields.Many2many(
        'res.users',
        'crm_lead_product_manager_rel',  # Explicit intermediary table name
        'lead_id',  # Column referring to this model
        'user_id',  # Column referring to the target model
        string='Product Manager',
        check_company=True
    )
    bid_team_assigned = fields.Many2many(
        'res.users',
        'crm_lead_bid_team_rel',  # Explicit intermediary table name
        'lead_id',  # Column referring to this model
        'user_id',  # Column referring to the target model
        string='Bid Team Assigned',
        check_company=True
    )
    division = fields.Many2many('division.name', relation='crm_lead_division_rel', column1='lead_id',
                                column2='user_id', string='Division')
    finance = fields.Many2many('res.users', 'crm_lead_finance_rel', 'lead_id', 'user_id', string='Finance Team',
                               domain=lambda self: [
                                   ("groups_id", "=", self.env.ref("flex_crm_custom.access_finance_manager").id)])

    @api.onchange('need_bid_point', 'value')
    def _onchange_need_bid_point(self):
        for rec in self:
            users = rec.finance
            opportunity_url = f"{rec.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={rec.name}&model=crm.lead&view_type=form"
            if rec.need_bid_point and rec.value and rec.value > 0.00:
                if rec.env.user.notification_type == 'email':
                    rec.env['mail.mail'].sudo().create({
                        'subject': 'Need Bid Point',
                        'email_from': rec.env.user.email,
                        'email_to': rec.finance.mapped('email'),
                        'body_html': f'<p><a href="{opportunity_url}">{rec.name}</a></p><p>Bid Point Name: {rec.subject}</p><p>Bid Point Value: {rec.value}</p><p>Vendors:{rec.vendor_opp.name}</p><p>Validity: {rec.validity.name}</p>',
                    }).send()
                elif rec.env.user.notification_type == 'inbox':
                    rec.env['mail.activity'].sudo().create({
                        'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                        'note': 'Bid Point Value',
                        'res_id': rec.id,
                        'res_model_id': rec.env.ref('crm.model_crm_lead').id,
                        'user_id': rec.user_ids.id,
                    })

    # request bid point
    need_bid_point = fields.Boolean(string='Need Bid Bond')
    subject = fields.Char(string='Subject')
    vendor_opp = fields.Many2many('res.partner', string='Vendor', related='vendor')
    value = fields.Float(string='Value')
    validity = fields.Many2one('validity', string='Validity')
    bid_purchase_request = fields.Boolean(string='Purchase Request')
    bid_purchase_subject = fields.Char(string='Purchase Subject')
    bid_purchase_value = fields.Float(string='Purchase Value')
    bid_purchase_deadline = fields.Date(string='Purchase Deadline')
    is_purchased_bid = fields.Boolean(string='Is Purchased')

    @api.onchange('is_purchased_bid')
    def onchange_is_purchased_bid(self):
        return {
            'warning': {
                'title': "Warning",
                'message': "This Field Is For Finance Team Are You Sure You Want To Change It?",
            }
        }


    @api.onchange('bid_purchase_request', 'bid_purchase_value')
    def _onchange_bid_purchase_request(self):
        for rec in self:
            users = rec.finance
            opportunity_url = f"{rec.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={rec.name}&model=crm.lead&view_type=form"
            if rec.bid_purchase_request and rec.bid_purchase_value and rec.bid_purchase_value > 0.00:
                if rec.env.user.notification_type == 'email':
                    rec.env['mail.mail'].sudo().create({
                        'subject': 'Bid Purchase Request',
                        'email_from': rec.env.user.email,
                        'email_to': rec.finance.mapped('email'),
                        'body_html': f'<p><a href="{opportunity_url}">{rec.name}</a></p><p>Purchase Request Name: {rec.bid_purchase_subject}</p><p>Purchase Request Value: {rec.bid_purchase_value}</p><p>Purchase Request Deadline: {rec.bid_purchase_deadline}</p>',
                    }).send()
                elif rec.env.user.notification_type == 'inbox':
                    rec.env['mail.activity'].sudo().create({
                        'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                        'note': 'Purchase Request Value',
                        'res_id': rec.id,
                        'res_model_id': rec.env.ref('crm.model_crm_lead').id,
                        'user_id': rec.user_ids.id,
                    })

    # dr register
    deal_id = fields.Char(string='Deal ID')
    deal_expiry = fields.Date(string='Deal Expiry')
    req_ext = fields.Boolean(string='Request Extension')

    @api.onchange('deal_expiry')
    def _onchange_deal_expiry(self):
        for rec in self:
            if rec.deal_expiry and rec._origin.deal_expiry and rec.deal_expiry != rec._origin.deal_expiry:
                if not rec.req_ext:
                    raise UserError(_('Please Check Request Extension'))

    # Tendaring
    need_tendering = fields.Boolean(string='Need Tendering')
    tendering_subject = fields.Char(string='Tendering Subject')
    tendering_state = fields.Selection([
        ('release', 'Release'),
        ('submit', 'Submit'),
        ('not_submit', 'Not Submit'),
    ], string='Tendering State', default='release')
    submit_deadline = fields.Date(string='Submission Deadline')
    delivery_method = fields.Selection([
        ('hard_copy', 'Hard Copy'),
        ('soft_copy', 'Soft Copy'),
        ('by_email', 'By Email'),
    ], string='Delivery Method')
    is_purchased = fields.Boolean(string='Is Purchased')
    clarification_deadline = fields.Date(string='Clarification Deadline')
    tender_purchase_request = fields.Boolean(string='Tender Purchase Request')
    purchase_subj = fields.Char(string='Purchase Subject')
    purchase_value = fields.Float(string='Purchase Value')
    purchase_deadline = fields.Date(string='Purchase Deadline')
    quarter = fields.Many2one('quartar', string='Quarter')
    expecting_close_date = fields.Date(string='Expecting Close')
    estimate_value = fields.Float(string='Estimate Value')

    @api.onchange('is_purchased')
    def onchange_is_purchased(self):
        return {
            'warning': {
                'title': "Warning",
                'message': "This Field Is For Finance Team Are You Sure You Want To Change It?",
            }
        }

    @api.onchange('tender_purchase_request', 'purchase_value')
    def onchange_tender_purchase_request(self):
        for rec in self:
            opportunity_url = f"{rec.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={rec.name}&model=crm.lead&view_type=form"
            if rec.tender_purchase_request and rec.purchase_value > 0.00:
                if rec.env.user.notification_type == 'email':
                    rec.env['mail.mail'].sudo().create({
                        'subject': 'Tender Purchase Request',
                        'email_from': rec.env.user.email,
                        'email_to': rec.finance.mapped('email'),
                        'body_html': f'<p>Opportunity Name: <a href="{opportunity_url}">{rec.name}</a></p><p>Purchase Request Name: {rec.purchase_subj}</p><p>Purchase Request Value: {rec.purchase_value}</p><p>Purchase Request Deadline: {rec.purchase_deadline}</p>',
                    }).send()
                elif rec.env.user.notification_type == 'inbox':
                    rec.env['mail.activity'].sudo().create({
                        'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                        'note': 'Purchase Request Value',
                        'res_id': rec.id,
                        'res_model_id': rec.env.ref('crm.model_crm_lead').id,
                        'user_id': rec.user_ids.id,
                    })

    @api.onchange('deal_id', 'deal_expiry')
    def _onchange_deal_id(self):

        if self.deal_id or self.deal_expiry and not self.env.user.has_group('flex_crm_custom.access_bid_manager'):
            return {
                'warning': {
                    'title': "Warning",
                    'message': "This Field Is For Bid Manager",
                }
            }

    def action_sale_account_manager(self):
        self.filtered(lambda so: so.state in ['sale_account_manager']).write({'state': 'business_unit_manager'})
        self.sale_account_manager = self.env.user
        for rec in self:
            if rec.env.user.notification_type == 'email':
                rec.env['mail.mail'].sudo().create({
                    'subject': 'Lead Name:' + " " + rec.name,
                    'email_from': rec.env.user.email,
                    'email_to': rec.bdm_manager.mapped('email'),
                    'body_html': f'</p><p>Need To Convert To Opportunity</p><p>Lead Name: {rec.name}</p><p>Lead ID: {rec.id}</p>',
                }).send()
            elif rec.env.user.notification_type == 'inbox':
                # add it for activity
                rec.env['mail.activity'].sudo().create({
                    'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                    'note': 'Need To Convert To Opportunity',
                    'res_id': rec.id,
                    'res_model_id': rec.env.ref('crm.model_crm_lead').id,
                    'user_id': rec.user_ids.id,
                })

    def action_opp(self):
        self.filtered(lambda so: so.state in ['business_unit_manager']).write({'state': 'opp'})

    def action_set_lost(self, **additional_values):
        res = self.action_archive()
        if additional_values:
            self.write(dict(additional_values))
        self.write({'state': 'lost'})
        return res

    def toggle_active(self):
        res = super(CrmLead, self).toggle_active()
        self.write({'state': 'opp'})
        return res

    def send_email(self):
        for rec in self:
            if rec.date_deadline and (rec.date_deadline - datetime.now().date()).days == 2 and rec.stage_id.id != 4:
                users = rec.sale_account_manager | rec.product_manager | rec.bid_team_assigned | rec.bdm_manager

                # Construct the opportunity URL
                base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
                opportunity_url = f"{base_url}/web#id={rec.id}&model=crm.lead&view_type=form"

                # Create the email body with hyperlink
                email_body = f"""
                    <p>Opportunity Name: {rec.name}</p>
                    <p>ID: <a href="{opportunity_url}">{rec.id}</a></p>
                    <p>Deadline: {rec.date_deadline}</p>
                """

                rec.env['mail.mail'].sudo().create({
                    'subject': 'Opportunity Deadline',
                    'body_html': email_body,
                    'email_to': ','.join(map(str, users.mapped('email'))),
                })

    def ten_pur_de(self):
        for rec in self:
            if rec.purchase_deadline and (
                    rec.purchase_deadline - datetime.now().date()).days == 1 and rec.tender_purchase_request:
                # Construct the opportunity URL
                base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
                opportunity_url = f"{base_url}/web#id={rec.name}&model=crm.lead&view_type=form"

                # Create the email body with hyperlink
                email_body = f"""
                    <p>Opportunity Name: <a href="{opportunity_url}">{rec.name}</a></p>
                    <p>Purchase Request Subject: {rec.purchase_subj}</p>
                    <p>Purchase Request Value: {rec.purchase_value}</p>
                    <p>Purchase Request Deadline: {rec.purchase_deadline}</p>
                """

                rec.env['mail.mail'].sudo().create({
                    'subject': 'Tender Purchase Request Deadline',
                    'body_html': email_body,
                    'email_to': ','.join(map(str, rec.finance.mapped('email'))),
                })

    def bid_pur_de(self):
        for rec in self:
            if rec.bid_purchase_deadline and (
                    rec.bid_purchase_deadline - datetime.now().date()).days == 1 and rec.bid_purchase_request:
                # Construct the opportunity URL
                base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
                opportunity_url = f"{base_url}/web#id={rec.name}&model=crm.lead&view_type=form"

                # Create the email body with hyperlink
                email_body = f"""
                    <p>Opportunity Name: <a href="{opportunity_url}">{rec.name}</a></p>
                    <p>Purchase Request Subject: {rec.bid_purchase_subject}</p>
                    <p>Purchase Request Value: {rec.bid_purchase_value}</p>
                    <p>Purchase Request Deadline: {rec.bid_purchase_deadline}</p>
                """

                rec.env['mail.mail'].sudo().create({
                    'subject': 'Bid Purchase Request Deadline',
                    'body_html': email_body,
                    'email_to': ','.join(map(str, rec.finance.mapped('email'))),
                })

    def deal_expiry_email(self):
        for rec in self:
            if rec.deal_expiry and (rec.deal_expiry - datetime.now().date()).days == 14 and rec.bid_team_assigned:
                users = rec.sale_account_manager | rec.product_manager | rec.bid_team_assigned | rec.bdm_manager

                base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
                opportunity_url = f"{base_url}/web#id={rec.id}&model=crm.lead&view_type=form"
                email_body = f"""
                    <p>Opportunity Name: {rec.name}</p>
                    <p>ID: <a href="{opportunity_url}">{rec.id}</a></p>
                    <p>Deal Expiry: {rec.deal_expiry}</p>
                """

                rec.env['mail.mail'].sudo().create({
                    'subject': 'Deal Expiry',
                    'email_from': rec.env.user.email,
                    'body_html': email_body,
                    'email_to': ','.join(map(str, users.mapped('email'))),
                })

    def onchange_need_tendering(self):
        for rec in self:
            users = rec.sale_account_manager | rec.product_manager | rec.bid_team_assigned | rec.bdm_manager

            if rec.submit_deadline and (rec.submit_deadline - datetime.now().date()).days == 2 and rec.need_tendering:
                # Construct the opportunity URL
                base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
                opportunity_url = f"{base_url}/web#id={rec.id}&model=crm.lead&view_type=form"
                email_body = f"""
                    <p>Opportunity Name: {rec.name}</p>
                    <p>Opportunity Name: <a href="{opportunity_url}">{rec.name}</a></p>
                    <p>Tendering Subject: {rec.tendering_subject}</p>
                    <p>Submission Tendering Deadline: {rec.submit_deadline}</p>
                    <p>Clarification Deadline: {rec.clarification_deadline}</p>
                """

                rec.env['mail.mail'].sudo().create({
                    'subject': 'Submission Deadline',
                    'email_from': rec.env.user.email,
                    'body_html': email_body,
                    'email_to': ','.join(map(str, rec.finance.mapped('email'))),
                })
            if rec.clarification_deadline and (
                    rec.clarification_deadline - datetime.now().date()).days == 2 and rec.need_tendering:
                # Construct the opportunity URL
                base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
                opportunity_url = f"{base_url}/web#id={rec.id}&model=crm.lead&view_type=form"
                email_body = f"""
                        <p>Opportunity Name: <a href="{opportunity_url}">{rec.name}</a></p>
                        <p>Tendering Subject: {rec.tendering_subject}</p>
                        <p>Clarification Deadline: {rec.clarification_deadline}</p>
                    """

                rec.env['mail.mail'].sudo().create({
                    'subject': 'Clarification Deadline',
                    'email_from': rec.env.user.email,
                    'body_html': email_body,
                    'email_to': ','.join(map(str, users.mapped('email'))),
                })

    def onchange_need_tendering_two(self):
        for rec in self:
            users = rec.sale_account_manager | rec.product_manager | rec.bid_team_assigned | rec.bdm_manager
            if rec.submit_deadline and (rec.submit_deadline - datetime.now().date()).days == 3 and rec.need_tendering:
                # Construct the opportunity URL
                base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
                opportunity_url = f"{base_url}/web#id={rec.id}&model=crm.lead&view_type=form"

                email_body = f"""
                    <p>Opportunity Name: <a href="{opportunity_url}">{rec.name}</a></p>
                    <p>Tendering Subject: {rec.tendering_subject}</p>
                    <p>Submission Tendering Deadline: {rec.submit_deadline}</p>
                """

                rec.env['mail.mail'].sudo().create({
                    'subject': 'Submission Deadline',
                    'email_from': rec.env.user.email,
                    'body_html': email_body,
                    'email_to': ','.join(map(str, rec.finance.mapped('email'))),
                })
            if rec.clarification_deadline and (
                    rec.clarification_deadline - datetime.now().date()).days == 3 and rec.need_tendering:
                # Construct the opportunity URL
                base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
                opportunity_url = f"{base_url}/web#id={rec.id}&model=crm.lead&view_type=form"

                email_body = f"""
                        <p>Opportunity Name: <a href="{opportunity_url}">{rec.name}</a></p>
                        <p>Tendering Subject: {rec.tendering_subject}</p>
                        <p>Clarification Deadline: {rec.clarification_deadline}</p>
                    """

                rec.env['mail.mail'].sudo().create({
                    'subject': 'Clarification Deadline',
                    'email_from': rec.env.user.email,
                    'body_html': email_body,
                    'email_to': ','.join(map(str, users.mapped('email'))),
                })

    def send_cron(self):
        crm_leads = self.env['crm.lead'].search([])
        for rec in crm_leads:
            rec.send_email()
            rec.deal_expiry_email()
            rec.onchange_need_tendering()
            rec.onchange_need_tendering_two()
            rec.ten_pur_de()
            rec.bid_pur_de()


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    user_ids = fields.Many2many(
        'res.users', string='Product Manager',
        # compute='_compute_user_id'
        readonly=False, compute_sudo=False,
        domain=lambda self: [("groups_id", "=", self.env.ref("flex_crm_custom.access_product_manager").id),

                             ])

    bid_team_assigneds = fields.Many2one(
        'res.users',
        string='Bid Team Assigned',
        domain=lambda self: [("groups_id", "=", self.env.ref("flex_crm_custom.access_bid_manager").id)],
    )
    name = fields.Selection([
        ('convert', 'Convert to opportunity'),
        ('merge', 'Merge with existing opportunities')
    ], 'Conversion Action', readonly=False, compute_sudo=False, default='convert')
    action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
        ('nothing', 'Do not link to a customer')
    ], string='Related Customer', readonly=False, compute_sudo=False, default='nothing')

    def action_apply(self):
        res = super(Lead2OpportunityPartner, self).action_apply()
        for rec in self:
            base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
            opportunity_url = f"{base_url}/web#id={rec.lead_id.id}&model=crm.lead&view_type=form"
            email_body = f"""
                <p>Opportunity Name: {rec.lead_id.name}</p>
                <p>ID: <a href="{opportunity_url}">{rec.lead_id.id}</a></p>
            """
            if rec.user_ids:
                if rec.env.user.notification_type == 'email':
                    rec.env['mail.mail'].sudo().create({
                        'subject': 'Opportunity Assigned As Product Manager From Business Division Manager',
                        'email_from': rec.env.user.email,
                        'email_to': rec.user_ids.mapped('email'),
                        'body_html': email_body,
                    })
                elif rec.env.user.notification_type == 'inbox':
                    rec.env['mail.activity'].sudo().create({
                        'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                        'note': email_body,
                        'res_id': rec.lead_id.id,
                        'res_model_id': rec.env.ref('crm.model_crm_lead').id,
                        'user_id': rec.user_ids.id,
                    })
            if rec.bid_team_assigneds:
                if rec.env.user.notification_type == 'email':
                    rec.env['mail.mail'].sudo().create({
                        'subject': 'Opportunity Assigned As Bid Team Assigned From Business Division Manager',
                        'email_from': rec.env.user.email,
                        'email_to': rec.bid_team_assigneds.mapped('email'),
                        'body_html': email_body,
                    })
                elif rec.env.user.notification_type == 'inbox':
                    rec.env['mail.activity'].sudo().create({
                        'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                        'note': email_body,
                        'res_id': rec.lead_id.id,
                        'res_model_id': rec.env.ref('crm.model_crm_lead').id,
                        'user_id': rec.user_ids.id,
                    })

        self.lead_id.check_active = True
        for rec in self:
            rec.lead_id.product_manager = rec.user_ids.ids
            rec.lead_id.bid_team_assigned = rec.bid_team_assigneds.ids
        return res

    @api.depends('user_ids')
    def _compute_team_id(self):
        for convert in self:
            if not convert.user_ids:
                continue
            users = convert.user_ids
            for user in users:
                if convert.team_id and (user in convert.team_id.member_ids or user == convert.team_id.user_id):
                    continue
                team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=None)
                convert.team_id = team.id

    def _action_merge(self):
        to_merge = self.duplicated_lead_ids
        result_opportunity = to_merge.merge_opportunity(auto_unlink=False)
        result_opportunity.action_unarchive()

        for rec in self:

            if result_opportunity.type == "lead":
                rec._convert_and_allocate(result_opportunity, [rec.user_ids.id], team_id=rec.team_id.id)
            else:
                if not result_opportunity.user_id or rec.force_assignment:
                    result_opportunity.write({
                        'user_id': rec.user_ids.id,
                        'team_id': rec.team_id.id,
                    })
            (to_merge - result_opportunity).sudo().unlink()

        return result_opportunity

    def _action_convert(self):
        """ """
        result_opportunities = self.env['crm.lead'].browse(self._context.get('active_ids', []))
        for rec in self:
            for user in rec.user_ids:
                rec._convert_and_allocate(result_opportunities, [user.id], team_id=rec.team_id.id)
        return result_opportunities[0]

    def _convert_and_allocate(self, leads, user_ids, team_id=False):
        self.ensure_one()

        for lead in leads:
            if lead.active and self.action != 'nothing':
                self._convert_handle_partner(
                    lead, self.action, self.partner_id.id or lead.partner_id.id)

            lead.convert_opportunity(lead.partner_id, user_ids=False, team_id=False)

        leads_to_allocate = leads
        if not self.force_assignment:
            leads_to_allocate = leads_to_allocate.filtered(lambda lead: not lead.user_id)

        if user_ids:
            leads_to_allocate._handle_salesmen_assignment(user_ids, team_id=team_id)

    def _convert_handle_partner(self, lead, action, partner_id):
        for rec in self:
            for user in rec.user_ids:
                lead.with_context(default_user_id=user.id)._handle_partner_assignment(
                    force_partner_id=partner_id,
                    create_missing=(action == 'create')
                )


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    def action_lost_reason_apply(self):
        res = super(CrmLeadLost, self).action_lost_reason_apply()
        return res


class Validity(models.Model):
    _name = 'validity'
    _description = 'Validity'

    name = fields.Char(string='Name')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Validity name already exists !"),
    ]
