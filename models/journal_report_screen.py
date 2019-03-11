# -*- coding: utf-8 -*-

from datetime import datetime
from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp.exceptions import UserError, AccessError



class JournalReportScreen(models.TransientModel):
    _name = 'journal.report.screen'
    _description = 'Stock Journal Report Screen'
    
    company_id = fields.Many2one('res.company', string="Company")
    org_ids = fields.Many2many('res.company', string="Organization")
    date_from = fields.Date(sting="Date From", default=fields.Datetime.now)
    date_to = fields.Date(sting="Date To", default=fields.Datetime.now)    
    report_id = fields.Many2one('stock.journal.report', string="Report Id")
    line_ids = fields.One2many('journal.report.screen.line','screen_id', string="Lines")
    
    @api.multi
    def action_print_xls(self):
        if self.report_id:
            return self.report_id.action_print()
        return False
    
class JournalReportScreenLine(models.TransientModel):
    _name = 'journal.report.screen.line'
    _description = 'Stock Journal Report Screen Line'
    
    sno = fields.Char('S.No')
    bill_date = fields.Date("In/Out Date")
    partner_id = fields.Many2one('res.partner', string='Supplier/Customer')
    inv_no = fields.Char(string='In/Out Inv No')
    # ~ reference_id = fields.Many2one('reference.master', string='Reference')
    main_product_id = fields.Many2one('product.product', string='Main Product Name')
    main_prod_qty = fields.Float('Main Product QTY')
    product_id = fields.Many2one('product.product', string='Sub Product Name')    
    inward_qty = fields.Float('Inward QTY')
    inward_price = fields.Float('Inward Price')
    inward_value = fields.Float('Inward Value')
    outward_qty = fields.Float('Outward QTY')
    outward_price = fields.Float('Outward Price')
    outward_value = fields.Float('Outward Value')
    balance = fields.Float('Balance QTY')
    balance_price = fields.Float('AVG Cost')
    balance_value = fields.Float('Balance Value')
    hide_bill = fields.Boolean('Hide Bill', default=False)
    hide_main_product = fields.Boolean('Hide Main Product', default=False)
    hide_product = fields.Boolean('Hide Product', default=False)
    stock_transfer_id = fields.Many2one('stock.transfer', string='Stock Journal')
    screen_id = fields.Many2one('journal.report.screen', string="Parent View") 
    
    
    
     
    

