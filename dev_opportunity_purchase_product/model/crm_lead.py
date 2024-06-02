# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://devintellecs.com>).
#
##############################################################################
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import itertools
import operator


class purchase_or(models.Model):
    _inherit = 'purchase.order'

    lead_id = fields.Many2one('crm.lead', string='Pipeline')


class crm_lead(models.Model):
    _inherit = 'crm.lead'

    purchase_line_ids = fields.One2many('crm.purchase.line', 'lead_pro_id')
    # po_flags = fields.Boolean(string='po flag', copy=False)
    po_ids = fields.One2many('purchase.order', 'lead_id', string='Purchase')
    po_count = fields.Integer(string='PO Orders', compute='_compute_po_count')

    @api.depends('po_ids')
    def _compute_po_count(self):
        for order in self:
            order.po_count = len(order.po_ids)

    def create_purchase_order(self):

        po_id = []
        line_ids = self._context.get('active_ids')
        vals = []
        for lead in self:
            if not lead.purchase_line_ids:
                raise UserError(_('Please add Purchase Quotation Line Products.'))
            pol_2b_created = lead.purchase_line_ids.filtered(lambda l: not l.is_po_created)
            if not pol_2b_created:
                raise UserError(_('RFQ(s) already created for all Purchase Quotation Lines.'))
            for line in pol_2b_created:
                if line.partner_id:
                    vals.append({
                        'partner_id': line.partner_id.id or '',
                        'product_id': line.product_id.id or '',
                        'product_qty': line.product_qty,
                        'product_uom': line.uom_id.id,
                        'price_unit': line.price_unit,
                        'name': line.name,
                        'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    })
            res = sorted(vals, key=operator.itemgetter('partner_id'))
            groups = itertools.groupby(res, key=operator.itemgetter('partner_id'))
            par_group = [{'partner_id': k, 'values': [x for x in v]} for k, v in groups]
            for vals in par_group:
                purchase_id = self.env['purchase.order'].create({
                    'partner_id': vals['partner_id'],
                    'lead_id': lead.id,
                })
                po_id.append(purchase_id.id)
                for line_val in vals['values']:
                    res = {
                        'product_id': line_val['product_id'],
                        'product_qty': line_val['product_qty'],
                        'product_uom': line_val['product_uom'],
                        'price_unit': line_val['price_unit'],
                        'name': line_val['name'],
                        'date_planned': line_val['date_planned'],
                        'order_id': purchase_id.id,
                    }
                    self.env['purchase.order.line'].create(res)

        #
        #             if self.po_flags == True:
        #                 raise UserError(_('Purchase Quotations already exist for this Opportunity'))
        #             self.write({'po_flags': True})

        # self.po_ids = po_id
        self.purchase_line_ids.write({'is_po_created': True})

        return {
            'name': 'New RFQs',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', po_id)],
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_type': 'form',

        }

    def purchase_order_status(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        po_ids = self.mapped('po_ids')
        if len(po_ids) > 1:
            action['domain'] = [('id', 'in', po_ids.ids)]
        elif po_ids:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = po_ids.id
        return action

    def send_mail_to_vendors(self):
        # if self.env.user.has_group('flex_crm_custom.access_bid_manager'):
        #     raise UserError(_('You are not allowed to send email to vendors.'))
        # else:
        for lead in self:

            opportunity_name = lead.name
            customer_name = lead.partner_id.name
            users = lead.sale_account_manager | lead.product_manager | lead.bid_team_assigned | lead.bdm_manager

            css_styles = """
                        <style>
                            .styled-table {
                                border-collapse: collapse;
                                width: 100%;
                            }
                            .styled-table th, .styled-table td {
                                padding: 8px;
                                text-align: left;
                                border-bottom: 1px solid #ddd;
                            }
                            .styled-table th {
                                background-color: #f2f2f2;
                            }
                            .styled-table tr:hover {
                                background-color: #f5f5f5;
                            }
                        </style>
                    """

            # Dictionary to hold partner_id and their corresponding product details
            partner_products = {}

            for line in lead.purchase_line_ids:
                partner_id = line.partner_id
                if partner_id:
                    if partner_id not in partner_products:
                        partner_products[partner_id] = []

                    product_info = f"<tr><td>{line.product_id.name}</td><td>{line.name}</td><td>{line.product_qty}</td><td>{line.product_id.qty_available}</td><td>{line.price_unit}</td></tr>"
                    partner_products[partner_id].append(product_info)

            # Send email per partner with all their products
            for partner_id, products in partner_products.items():
                body_html = f"{css_styles}<table class='styled-table'><tr><th>Product</th><th>Description</th><th>Quantity</th><th>Available Quantity</th><th>Unit Price</th></tr>{''.join(products)}</table>"

                partner_id.env['mail.mail'].sudo().create({
                    'subject': 'Product Opportunity',
                    'email_from': partner_id.env.user.email,
                    'email_cc': ','.join(users.mapped('email')) if users else '',
                    'email_to': partner_id.email,
                    'body_html': f'<p>This Product Is Available in Opportunity {opportunity_name}</p><p>Customer Name: {customer_name}</p><p>{body_html}</p>'
                }).send()

    def send_mail_to_distribution(self):
        for lead in self:
            opportunity_name = lead.name
            customer_name = lead.partner_id.name
            users = lead.sale_account_manager | lead.product_manager | lead.bid_team_assigned | lead.bdm_manager

            css_styles = """
                    <style>
                        .styled-table {
                            border-collapse: collapse;
                            width: 100%;
                        }
                        .styled-table th, .styled-table td {
                            padding: 8px;
                            text-align: left;
                            border-bottom: 1px solid #ddd;
                        }
                        .styled-table th {
                            background-color: #f2f2f2;
                        }
                        .styled-table tr:hover {
                            background-color: #f5f5f5;
                        }
                    </style>
                """

            # Dictionary to hold partner_id and their corresponding product details
            partner_products = {}

            for line in lead.purchase_line_ids:
                partner_id = line.distribution_id
                if partner_id:
                    if partner_id not in partner_products:
                        partner_products[partner_id] = []

                    product_info = f"<tr><td>{line.product_id.name}</td><td>{line.name}</td><td>{line.product_qty}</td><td>{line.product_id.qty_available}</td><td>{line.price_unit}</td></tr>"
                    partner_products[partner_id].append(product_info)

            # Send email per partner with all their products
            for partner_id, products in partner_products.items():
                body_html = f"{css_styles}<table class='styled-table'><tr><th>Product</th><th>Description</th><th>Quantity</th><th>Available Quantity</th><th>Unit Price</th></tr>{''.join(products)}</table>"

                partner_id.env['mail.mail'].sudo().create({
                    'subject': 'Product Opportunity',
                    'email_from': partner_id.env.user.email,
                    'email_cc': ','.join(users.mapped('email')) if users else '',
                    'email_to': partner_id.email,
                    'body_html': f'<p>This Product Is Available in Opportunity {opportunity_name}</p><p>Customer Name: {customer_name}</p><p>{body_html}</p>'
                }).send()

    def send_mail_to_all(self):
        for rec in self:
            if rec.purchase_line_ids.partner_id:
                rec.send_mail_to_vendors()
            if rec.purchase_line_ids.distribution_id:
                rec.send_mail_to_distribution()


class crm_lead_line(models.Model):
    _name = 'crm.purchase.line'

    lead_pro_id = fields.Many2one('crm.lead')
    partner_id = fields.Many2one('res.partner', string="Vendor")
    product_id = fields.Many2one('product.product', string="Sq Line", required=True)
    distribution_id = fields.Many2one('res.partner', string='Distribute')
    product_qty = fields.Float(string="QTY", required=True, default=1)
    uom_id = fields.Many2one('uom.uom', string="Product UOM", required=True)
    # price_unit = fields.Many2one('product.uom', string="Product UOM", required=True)
    price_unit = fields.Float(string="Unit Price", required=True)
    name = fields.Char(string="Description", required=True)
    date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    is_po_created = fields.Boolean(string="PO Created", default=False)

    # @api.onchange('partner_id', 'product_id', 'product_qty', 'uom_id')
    # def _get_price(self):
    #     for seller in self.product_id.seller_ids:
    #         if self.partner_id == seller.name and self.product_qty == seller.min_qty and self.uom_id == seller.product_uom:
    #             self.price_unit = seller.price
    #         else:
    #             self.price_unit = 0.0

    @api.onchange('partner_id', 'product_id', 'product_qty', 'uom_id')
    def _get_price(self):
        if not (self.partner_id and self.product_id and self.product_qty and self.uom_id):
            self.price_unit = 0.0
            return

        for seller in self.product_id.seller_ids:
            if (self.partner_id == seller.partner_id and
                    self.product_qty >= seller.min_qty and
                    self.uom_id == seller.product_uom):
                self.price_unit = seller.price
                break
        else:
            self.price_unit = 0.0

    @api.onchange('product_id')
    def product_id_change(self):
        result = {}
        if self.product_id:
            self.uom_id = self.product_id.uom_id and self.product_id.uom_id.id or ''
            self.name = self.product_id.name or ''

    def send_email_to_vendor(self):
        for lead in self:
            opportunity_name = lead.lead_pro_id.name
            customer_name = lead.lead_pro_id.partner_id.name
            users = lead.lead_pro_id.sale_account_manager | lead.lead_pro_id.product_manager | lead.lead_pro_id.bid_team_assigned | lead.lead_pro_id.bdm_manager
            css_styles = """
               <style>
                   .styled-table {
                       border-collapse: collapse;
                       width: 100%;
                   }
                   .styled-table th, .styled-table td {
                       padding: 8px;
                       text-align: left;
                       border-bottom: 1px solid #ddd;
                   }
                   .styled-table th {
                       background-color: #f2f2f2;
                   }
                   .styled-table tr:hover {
                       background-color: #f5f5f5;
                   }
               </style>
               """
            # create a table with the product details in body_html
            # body_html = "<table border='1'><tr><th>Product</th><th>Description</th><th>Quantity</th><th>Available Quantity</th><th>Unit Price</th></tr><tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr></table>".format(
            #     lead.product_id.name, lead.name, lead.product_qty, lead.product_id.qty_available, lead.price_unit)
            # for line in lead:
            #     line.env['mail.mail'].sudo().create({
            #         'subject': 'Product Opportunity',
            #         'email_from': line.env.user.email,
            #         'email_to': line.partner_id.email,
            #         'body_html': f'</p><p>This Products Is Available in Opportunity {opportunity_name}</p><p><p>{body_html}</p></p>'
            #     }).send()
            body_html = f"{css_styles}<table class='styled-table'><tr><th>Product</th><th>Description</th><th>Quantity</th><th>Available Quantity</th><th>Unit Price</th></tr><tr><td>{lead.product_id.name}</td><td>{lead.name}</td><td>{lead.product_qty}</td><td>{lead.product_id.qty_available}</td><td>{lead.price_unit}</td></tr></table>"
            for line in lead:
                if line.partner_id:
                    line.env['mail.mail'].sudo().create({
                        'subject': 'Product Opportunity',
                        'email_from': line.env.user.email,
                        'email_to': line.partner_id.email,
                        'email_cc': ','.join(users.mapped('email')) if users else '',
                        'body_html': f'</p><p>This Product Is Available in Opportunity {opportunity_name}</p><p>Customer Name:{customer_name}</p><p><p>{body_html}</p></p>'
                    }).send()

    def send_email_to_distribution(self):
        for lead in self:
            opportunity_name = lead.lead_pro_id.name
            customer_name = lead.lead_pro_id.partner_id.name
            users = lead.lead_pro_id.sale_account_manager | lead.lead_pro_id.product_manager | lead.lead_pro_id.bid_team_assigned | lead.lead_pro_id.bdm_manager
            css_styles = """
               <style>
                   .styled-table {
                       border-collapse: collapse;
                       width: 100%;
                   }
                   .styled-table th, .styled-table td {
                       padding: 8px;
                       text-align: left;
                       border-bottom: 1px solid #ddd;
                   }
                   .styled-table th {
                       background-color: #f2f2f2;
                   }
                   .styled-table tr:hover {
                       background-color: #f5f5f5;
                   }
               </style>
               """
            # create a table with the product details in body_html
            # body_html = "<table border='1'><tr><th>Product</th><th>Description</th><th>Quantity</th><th>Available Quantity</th><th>Unit Price</th></tr><tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr></table>".format(
            #     lead.product_id.name, lead.name, lead.product_qty, lead.product_id.qty_available, lead.price_unit)
            # for line in lead:
            #     line.env['mail.mail'].sudo().create({
            #         'subject': 'Product Opportunity',
            #         'email_from': line.env.user.email,
            #         'email_to': line.partner_id.email,
            #         'body_html': f'</p><p>This Products Is Available in Opportunity {opportunity_name}</p><p><p>{body_html}</p></p>'
            #     }).send()
            body_html = f"{css_styles}<table class='styled-table'><tr><th>Product</th><th>Description</th><th>Quantity</th><th>Available Quantity</th><th>Unit Price</th></tr><tr><td>{lead.product_id.name}</td><td>{lead.name}</td><td>{lead.product_qty}</td><td>{lead.product_id.qty_available}</td><td>{lead.price_unit}</td></tr></table>"
            for line in lead:
                if line.distribution_id:
                    line.env['mail.mail'].sudo().create({
                        'subject': 'Product Opportunity',
                        'email_from': line.env.user.email,
                        'email_cc': ','.join(users.mapped('email')) if users else '',
                        'email_to': line.distribution_id.email,
                        'body_html': f'</p><p>This Product Is Available in Opportunity {opportunity_name}</p><p>Customer Name:{customer_name}</p><p><p>{body_html}</p></p>'
                    }).send()

    def send_mail_to_all(self):
        for rec in self:
            if rec.partner_id:
                rec.send_email_to_vendor()
            if rec.distribution_id:
                rec.send_email_to_distribution()


class InheritOrderLine(models.Model):
    _inherit = 'sale.order.line'

    route_id = fields.Many2one('stock.location.route', string='Route', domain=[('sale_selectable', '=', True)],
                               ondelete='restrict', check_company=True, required=False)

# class Lead2OpportunityPartner(models.TransientModel):
#     _inherit = 'crm.lead2opportunity.partner'
#
#     def action_apply(self):
#         res = super(Lead2OpportunityPartner, self).action_apply()
#         # send email to each vendor in purchase_line_ids with product
#         for lead in self.lead_id:
#             opportunity_name = lead.name
#             for line in lead.purchase_line_ids:
#                 product = line.product_id
#                 if line.partner_id:
#                     line.env['mail.mail'].sudo().create({
#                         'subject': 'Product Opportunity',
#                         'email_from': line.env.user.email,
#                         'email_to': line.partner_id.email,
#                         'body_html': f'</p><p>This Product {product.name} Is Available in Opportunity {opportunity_name}</p>'
#                     }).send()
#         return res
