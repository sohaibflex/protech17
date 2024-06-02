# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Purchase Quote from CRM LEAD/Opportunity',
    'version': '17.0.1.0',
    'sequence': 1,
    'category': 'Purchases',
    'description':
        """
        This Module add below functionality into odoo

        1.Create Purchase Order from Opportunity\n

odoo app allow to create Purchase Quotation from lead/Opportunity, purchase crm, purchase from lead, purchase from Opportunity, rfq from lead, quotation from lead, rfq from opportunity, rfq lead,lead purchase, crm purchase, opportunity purchase

    """,
    'summary': 'odoo app allow to create Purchase Quotation from lead/Opportunity, purchase crm, purchase from lead, purchase from Opportunity, rfq from lead, quotation from lead, rfq from opportunity, rfq lead,lead purchase, crm purchase, opportunity purchase',
    'depends': ['crm', 'purchase', 'sale_crm','flex_crm_custom'],
    'data': [
        'security/ir.model.access.csv',
        'view/crm_lead.xml',
        'view/purchase_order.xml',
        ],
    'demo': [],
    'test': [],
    # 'css': [],
    # 'qweb': [],
    # 'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':8.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
