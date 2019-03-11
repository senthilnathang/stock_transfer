# -*- coding: utf-8 -*-


{
    'name': 'Stock Transfer from One Product to Another',
    'version': '1.0',
    'website': '',
    'category': 'Warehouse',
    'author': 'TenthPlanet',
    'sequence': 10,
    'summary': 'Product Stock Move',
    'depends': ['account',
    # ~ 'jainerp_stock','jainerp_sales','reference_master'
    ],
    'description': """
Manage the Stock Transfer process in Odoo
=========================================

The stock transfer module allows you to move one or more products stock into another product(s)
    """,
    'data': [
        'security/stock_transfer_security.xml',
        'views/stock_transfer_view.xml',
        'data/stock_transfer_sequence.xml',
        'views/stock_journal_report_views.xml',
        'report/stock_transfer_report.xml',
        'views/journal_report_screen_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'test': [ ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
