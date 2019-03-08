{
    'name':'Stock Transfer',
    'description':"Stock Transfer",
    'category': 'Warehouse',
    'sequence': 10,
    'version':'1.1',
    'author':'Senthilnathan G',
    'website':'http://senthilnathan.co',
    'data': [
		# ~ 'security/ir.model.access.csv',
        'views/stock_move_views.xml',
        'views/stock_transfer_view.xml',
       
    ],
    'qweb': [
    ],
    'depends': ['sale','product','stock'],
    'images': [
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
