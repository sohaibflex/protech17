{
    'name': 'Flex CRM Task',
    'version': '17.0.0.0',
    'summary': '',
    'description': 'Make Ability To Create Taskes Form CRM',
    'category': '',
    'author': 'Sohaib Alamleh||Flex-ops',
    'website': 'https://www.flexops.com',
    'license': '',
    'depends': ['base', 'crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead.xml',
        'wizard/task.xml',
    ],
    'demo': [''],
    'installable': True,
    'auto_install': False,
}
