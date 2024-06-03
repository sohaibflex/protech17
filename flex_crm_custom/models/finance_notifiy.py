from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.onchange('is_purchased_bid')
    def onchange_is_purchased_bid(self):
        for rec in self:
            if rec.is_purchased_bid:
                opportunity_url = f"{rec.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={rec.name}&model=crm.lead&view_type=form"
                users = rec.sale_account_manager | rec.product_manager | rec.bid_team_assigned | rec.bdm_manager
                if rec.env.user.notification_type == 'email':
                    rec.env['mail.mail'].sudo().create({
                        'subject': 'Bid Purchase Is Issued',
                        'email_from': rec.env.user.email,
                        'email_to': ','.join(map(str, users.mapped('email'))),
                        'body_html': f'<p>Opportunity Name: <a href="{opportunity_url}">{rec.name}</a></p><p>Purchase Request Name: {rec.bid_purchase_subject}</p><p>Purchase Request Value: {rec.bid_purchase_value}</p><p>Purchase Request Deadline: {rec.bid_purchase_deadline}</p>',
                    }).send()
                elif rec.env.user.notification_type == 'inbox':
                    rec.env['mail.message'].sudo().create({
                        'subject': 'Bid Purchase Is Issued',
                        'body': f'Opportunity Name: {rec.name}\nPurchase Request Name: {rec.bid_purchase_subject}\nPurchase Request Value: {rec.bid_purchase_value}\nPurchase Request Deadline: {rec.bid_purchase_deadline}',
                        'model': 'crm.lead',
                        'res_id': rec.id,
                        'message_type': 'notification',
                        'subtype_id': rec.env.ref('mail.mt_note').id,
                        'partner_ids': [(6, 0, ','.join(map(str, users.mapped('partner_id').ids)))],
                    })

    @api.onchange('is_purchased')
    def onchange_is_purchased(self):
        for rec in self:
            if rec.is_purchased:
                opportunity_url = f"{rec.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={rec.name}&model=crm.lead&view_type=form"
                users = rec.sale_account_manager | rec.product_manager | rec.bid_team_assigned | rec.bdm_manager
                if rec.env.user.notification_type == 'email':
                    rec.env['mail.mail'].sudo().create({
                        'subject': 'Tender Purchase Is Issued',
                        'email_from': rec.env.user.email,
                        'email_to': ','.join(map(str, users.mapped('email'))),
                        'body_html': f'<p>Opportunity Name: <a href="{opportunity_url}">{rec.name}</a></p><p>Purchase Request Name: {rec.purchase_subj}</p><p>Purchase Request Value: {rec.purchase_value}</p><p>Purchase Request Deadline: {rec.purchase_deadline}</p>',
                    }).send()
                elif rec.env.user.notification_type == 'inbox':
                    rec.env['mail.message'].sudo().create({
                        'subject': 'Tender Purchase Is Issued',
                        'body': f'Opportunity Name: {rec.name}\nPurchase Request Name: {rec.purchase_subj}\nPurchase Request Value: {rec.purchase_value}\nPurchase Request Deadline: {rec.purchase_deadline}',
                        'model': 'crm.lead',
                        'res_id': rec.id,
                        'message_type': 'notification',
                        'subtype_id': rec.env.ref('mail.mt_note').id,
                        'partner_ids': [(6, 0, ','.join(map(str, users.mapped('partner_id').ids)))],
                    })
