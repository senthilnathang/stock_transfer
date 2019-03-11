# -*- coding: utf-8 -*-

from datetime import datetime
from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp.exceptions import UserError, AccessError



class StockJournalReport(models.TransientModel):
    _name = 'stock.journal.report'
    _description = 'Stock Journal Report'
    
    company_id = fields.Many2one('res.company', string="Company", ondelete="restrict", default=lambda self: self.env.user.company_id, required=True)
    org_id = fields.Many2one('res.company', string="Organization", ondelete="restrict")
    product_ids = fields.Many2many('product.product', string="Products")
    date_from = fields.Date(sting="Date From", default=fields.Datetime.now)
    date_to = fields.Date(sting="Date To", default=fields.Datetime.now)    
    include_draft = fields.Boolean(string="Include Draft State", default=False)
    # ~ reference_ids = fields.Many2many('reference.master', string="Tracking Ids")
    
    def action_print(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': ids}
        datas['model'] = 'stock.journal.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':context.get('active_ids',False)})
        return {'type': 'ir.actions.report.xml', 'report_name': 'stock_transfer.stock_journal_report_xls', 'datas': datas}
    
    @api.multi
    def action_preview(self):
        line_ids = org_ids = []
        res = self.get_result()
        sino = balance = tot_inward = tot_outward = in_sub_total = out_sub_total = 0
        product_dict = {}
        remove_dup_main_prod = {}
        remove_dup_data = {}
        bill_dict = {}
        sino = 0
        for line in res:
            
            hide_bill = hide_main_product = hide_product = False             
            in_qty = out_qty = 0           
            if line.get('sub_prod_id', False) in product_dict:
                if line.get('inward',False):
                    in_qty = line.get('sub_prod_qty')
                    product_dict[line['sub_prod_id']] = product_dict[line['sub_prod_id']] + line.get('sub_prod_qty')
                elif line.get('outward',False):
                    out_qty = line.get('sub_prod_qty')
                    product_dict[line['sub_prod_id']] = product_dict[line['sub_prod_id']] - line.get('sub_prod_qty')
            elif not line.get('sub_prod_id', False) in product_dict:
                if line.get('inward',False):
                    in_qty = line.get('sub_prod_qty')
                    product_dict[line['sub_prod_id']] = line.get('sub_prod_qty')
                elif line.get('outward',False):
                    out_qty = line.get('sub_prod_qty')
                    product_dict[line['sub_prod_id']] = -line.get('sub_prod_qty')
            
            if line.get('transfer_id', False) and line.get('inward',False):
                if line.get('transfer_id') in remove_dup_main_prod:
                    hide_bill = True
                    hide_main_product = True                     
                elif not line.get('transfer_id') in remove_dup_main_prod:
                    remove_dup_main_prod[line['transfer_id']] = line.get('transfer_id')
                    sino += 1  
             
            if line.get('pick_id', False) and (line.get('outward',False) or line.get('inward',False)):
                if line.get('pick_id') in remove_dup_data:
                    hide_bill = True
                    hide_main_product = True
                     
                elif not line.get('pick_id') in remove_dup_data:
                    remove_dup_data[line['pick_id']] = line.get('pick_id')
                    sino += 1
            if not line['main_prod_id']:
                hide_main_product = True
                          
            balance = product_dict[line['sub_prod_id']] 

            line_vals = {'hide_bill': hide_bill, 'hide_main_product': hide_main_product, 'hide_product': hide_product,
                         'sno': sino, 'bill_date': line['in_out_date'], 'partner_id': line['partner_id'], 'inv_no': line['inv_no'],
                         'reference_id': line['reference_id'], 'main_product_id': line['main_prod_id'], 'main_prod_qty': line['main_prod_qty'], 
                         'product_id': line['sub_prod_id'], 'inward_qty': in_qty, 'inward_price': line['in_price_unit'], 'inward_value': line['in_subtotal'],
                          'outward_qty': out_qty, 'outward_price': line['out_price_unit'], 'outward_value': line['out_subtotal'],                         
                         'balance': balance, 'balance_price': 0, 'balance_value': 0,
                         'stock_transfer_id': line['stock_transfer_id']
                         }
            line_ids.append((0, 0, line_vals))    
                
        
        if self.org_id:
            org_ids = [(6, 0, self.org_id.ids)]
        else:
            org_ids = [(6, 0, self.env['res.company'].search([('parent_id','=',self.company_id.id)]).ids)]
        vals = {
                'line_ids': line_ids,
                'date_from': self.date_from or False,                
                'date_to': self.date_to or False,
                'company_id': self.company_id.id,
                'org_ids': org_ids,
                'report_id': self.id,
                }
        
        screen_id = self.env['journal.report.screen'].create(vals)
        result = self.env['ir.model.data'].get_object_reference('stock_transfer', 'journal_report_screen_view')
        return {
            'name': 'Stock Journal Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'journal.report.screen',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_id': result and result[1] or False,
            'res_id': screen_id.id,
        }    
    
    @api.multi
    def get_result(self):
        objects = self
        states = "('done')"
        stj_states = "('done')"
        reference_caluse = ''
        stj_reference_caluse = ''
        org_caluse = ''
        stj_org_caluse = ''
        product_caluse = ''
        stj_product_caluse = ''
        loc_clause = ''
        stj_loc_clause = ''
        if len(objects.product_ids) == 1:
            product_caluse = ' and sm.product_id = '+str(objects.product_ids.id)
            stj_product_caluse = ' and sm1.product_id = '+str(objects.product_ids.id)
        elif len(objects.product_ids) > 1:
            stj_product_caluse = ' and sm1.product_id in ' +str(tuple(objects.product_ids.ids))
            product_caluse = ' and sm.product_id in ' +str(tuple(objects.product_ids.ids))
        
        if objects.org_id:
            stj_org_caluse = ' and st.org_id = '+str(objects.org_id.id)
            org_caluse = ' and sp.org_id = '+str(objects.org_id.id)
            loc_ids = self.env['stock.location'].search([('org_id','=',objects.org_id.id)])
            if len(loc_ids) == 1:
                loc_clause = ' and sl.id = '+str(loc_ids.id)
            elif len(loc_ids) > 1:
                loc_clause = ' and sl.id in '+str(tuple(loc_ids.ids))
        if objects.include_draft:
            states = "('draft','waiting','confirmed','partially_available','assigned','done')"
            stj_states = "('draft','partially_available','available','done')"
        if objects.reference_ids:
            if len(objects.reference_ids) == 1:
                stj_reference_caluse = " and st.reference_id = "+str(objects.reference_ids.id)
                reference_caluse = " and sm.reference_id = "+str(objects.reference_ids.id)
            elif len(objects.reference_ids) > 1:
                stj_reference_caluse = " and st.reference_id in "+str(tuple(objects.reference_ids.ids))
                reference_caluse = " and sm.reference_id in "+str(tuple(objects.reference_ids.ids))
 
        sql = '''
                select * from (
                    select to_char(st.date,'YYYY-MM-DD') as in_out_date, st.create_date, rp.name as partner, rp.id as partner_id, st.inv_no as inv_no, st.id as stock_transfer_id,
                    pt.name as main_prod_name, pp.id as main_prod_id, sm.product_uom_qty as main_prod_qty,
                    pt1.name as sub_prod_name, pp1.id as sub_prod_id, sm1.product_uom_qty as sub_prod_qty,
                    sm1.price_unit as in_price_unit, (sm1.product_uom_qty*sm1.price_unit) as in_subtotal, 0 as out_price_unit, 0 as out_subtotal,
                    rm.name as reference,rm.ref, rm.id as reference_id,sm.name as move_name, True as inward, False as outward, st.id as transfer_id, null as pick_id
                    from stock_transfer st
                    inner join reference_master rm on rm.id=st.reference_id
                    left join res_partner rp on rp.id=st.partner_id
                    inner join stock_move sm on sm.input_transfer_id = st.id
                    inner join product_product pp on pp.id=sm.product_id
                    inner join product_template pt on pt.id=pp.product_tmpl_id
                    
                    inner join stock_move sm1 on sm1.output_transfer_id = st.id
                    inner join product_product pp1 on pp1.id=sm1.product_id
                    inner join product_template pt1 on pt1.id=pp1.product_tmpl_id
                    where st.company_id = %s and st.state in %s %s %s %s 
                     and st.date >= '%s' and st.date <= '%s'
                     
                    union all
                    
                    select to_char(sm.date,'YYYY-MM-DD') as in_out_date, sm.create_date, rp.name as partner, rp.id as partner_id, concat(sp.origin, ' --> ', sp.invoice_no) as inv_no, null as stock_transfer_id,
                    '' as main_prod_name, null as main_prod_id, 0 as main_prod_qty,
                    pt.name as sub_prod_name, pp.id as sub_prod_id, sm.product_uom_qty as sub_prod_qty,
                    0 as in_price_unit, 0 as in_subtotal, sm.price_unit as out_price_unit, (sm.product_uom_qty*sm.price_unit) as out_subtotal,  
                    rm.name as reference,rm.ref, rm.id as reference_id,sm.name as move_name, False as inward, True as outward, null as transfer_id, sp.id as pick_id
                    from stock_move sm 
                    inner join stock_picking sp on sp.id=sm.picking_id
                    left join res_partner rp on rp.id=sp.partner_id
                    inner join reference_master rm on rm.id=sm.reference_id
                    inner join stock_location sl on sl.id=sm.location_id
                    inner join product_product pp on pp.id=sm.product_id
                    inner join product_template pt on pt.id=pp.product_tmpl_id
                    where sm.company_id = %s and sm.reference_id is not null and sl.usage = 'internal' and sm.state in %s %s %s %s
                     and to_char(sp.date, 'YYYY-MM-DD') >= '%s' and to_char(sp.date, 'YYYY-MM-DD') <= '%s'
                    
                    union all
    
                    select to_char(sm.date,'YYYY-MM-DD') as in_out_date, sm.create_date, rp.name as partner, rp.id as partner_id, concat(sp.origin, ' --> ', sp.invoice_no) as inv_no, null as stock_transfer_id,
                    '' as main_prod_name, null as main_prod_id, 0 as main_prod_qty,
                    pt.name as sub_prod_name, pp.id as sub_prod_id, sm.product_uom_qty as sub_prod_qty,
                    sm.price_unit as in_price_unit, (sm.product_uom_qty*sm.price_unit) as in_subtotal, 0 as out_price_unit, 0 as out_subtotal,
                    rm.name as reference,rm.ref, rm.id as reference_id,sm.name as move_name, True as inward, False as outward, null as transfer_id, sp.id as pick_id
                    from stock_move sm 
                    inner join stock_picking sp on sp.id=sm.picking_id
                    left join res_partner rp on rp.id=sp.partner_id
                    inner join reference_master rm on rm.id=sm.reference_id
                    inner join stock_location sl on sl.id=sm.location_dest_id
                    inner join product_product pp on pp.id=sm.product_id
                    inner join product_template pt on pt.id=pp.product_tmpl_id
                    where sm.company_id = %s and sm.reference_id is not null and sl.usage = 'internal' and sm.state in %s %s %s %s
                     and to_char(sp.date, 'YYYY-MM-DD') >= '%s' and to_char(sp.date, 'YYYY-MM-DD') <= '%s'
                 ) as temp order by in_out_date asc,create_date asc
                '''%(objects.company_id.id, stj_states, stj_reference_caluse, stj_product_caluse, stj_org_caluse, objects.date_from, objects.date_to,
                     objects.company_id.id, states, reference_caluse, product_caluse, loc_clause, objects.date_from, objects.date_to,
                     objects.company_id.id, states, reference_caluse, product_caluse, loc_clause, objects.date_from, objects.date_to) 
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()
    

