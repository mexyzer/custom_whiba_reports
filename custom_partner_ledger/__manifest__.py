# -*- coding: utf-8 -*-
{
    'name': "Custom Partner Ledger Custom",
    'summary': "Custom Partner Ledger Custom",
    'description': "Custom Partner Ledger Custom",
    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway.co",
    'category': 'Accounting',
    'version': '1.0',
    'license': "Other proprietary",
    'depends': ['base', 'account_reports'],
    'data': [

        'security/ir.model.access.csv',
        'wizard/partner_ledger_wizard_view.xml',

        "views/partner_ledger_layout.xml",
        "views/partner_ledger_template.xml",
        'report/report_partnerledger.xml'
    ],
}
