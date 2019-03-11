# -*- coding: utf-8 -*-

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    ReportXlsx = object
from openerp.report import report_sxw
from openerp import _
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import xlsxwriter 
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class StockJournalReportXlsx(ReportXlsx):
    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(ReportXlsx, self).__init__(
            name, table, rml, parser, header, store)

        self.sheet = None
        self.row_pos = None

        self.format_title = None
        self.format_border_top = None

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Available formats:
         * format_title
         * format_header
         * format_header_right
         * format_header_italic
         * format_border_top
        """
        self.format_title_main_center = workbook.add_format({
            'bold': True,
            'align': 'left',
            'font_size': 14,
            'border': True,
            'font_name':'Arial',
            'align': 'Center',
            'bg_color': '#D8D7D7',
        })
        self.format_title = workbook.add_format({
            'align': 'left',
            'font_size': 12,
            'border': True,
            'font_name':'Arial',
            'text_wrap': True
        })
        self.format_title_noborder = workbook.add_format({
            'align': 'left',
            'font_size': 12,
            'border': False,
            'font_name':'Arial'
        })
        self.format_title_noborder_bold = workbook.add_format({
            'align': 'left',
            'font_size': 12,
            'bold': True,
            'border': False,
            'font_name':'Arial'
        })
        self.format_title_center = workbook.add_format({
            'align': 'left',
            'font_size': 12,
            'border': True,
            'align': 'Center',
            'font_name':'Arial'
        })
        self.format_title_bold = workbook.add_format({
            'align': 'left',
            'font_size': 12,
            'border': True,
            'font_name':'Arial',
            'bold': True,
        })
        self.format_title_center_bold = workbook.add_format({
            'align': 'left',
            'font_size': 12,
            'border': True,
            'font_name':'Arial',
            'align': 'Center',
            'bold': True,
        })
        self.format_title_number = workbook.add_format({
            'align': 'right',
            'font_size': 12,
            'border': True,
            'font_name':'Arial',
            'num_format': '#,##0.00',
        })
        self.format_title_number_bold = workbook.add_format({
            'align': 'right',
            'font_size': 12,
            'border': True,
            'font_name':'Arial',
            'num_format': '#,##0.00',
            'bold': True,
            'bg_color': '#D8D7D7',
        })
        
        self.format_header = workbook.add_format({
            'bold': True,
            'border': True,
            'font_name':'Arial',
            'font_size': 12,
            'align': 'Center',
            'bg_color': '#D8D7D7',        
        })

        self.merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        
    def convert_date_format(self, date):
        if date:
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%d/%m/%Y')
        
    def _write_report_title_center(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, 10, title, self.format_title_main_center
        )
        self.row_pos += 1
        
    def _write_report_subtitle(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, 10, title, self.format_title_center
        )
        self.row_pos += 1 
    
    def _write_report_subtitle_bold(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, 10, title, self.format_title_center_bold
        )
        self.row_pos += 1
    
    def _write_report_subtitle_bold_background(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, 10, title, self.format_header
        )
        self.row_pos += 1
        
    def _write_report_range(self, date1, date2):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, 10,_('')+date1+_(' To ')+date2+_(''), self.format_title)
    
    def _write_report_mergerows(self, val, row1, row2, column):
        self.sheet.merge_range(row1, column, row2, column,_('')+val+_(''), self.format_title)
    
    def _write_report_mergerows_header(self, val, row1, row2, column):
        self.sheet.merge_range(row1, column, row2, column,_('')+val+_(''), self.format_header)
        
    def _write_report_mergecols(self, val, col1, col2):
        self.sheet.merge_range(self.row_pos, col1, self.row_pos, col2,_('')+val+_(''), self.format_title)
        
    def _write_report_mergecols_header(self, val, col1, col2):
        self.sheet.merge_range(self.row_pos, col1, self.row_pos, col2,_('')+val+_(''), self.format_header)
            
    def _write_report_merge2_noborder(self, val, col1, col2):
        self.sheet.merge_range(
            self.row_pos, col1, self.row_pos, col2,_('')+val+_(''), self.format_title_noborder)
    
    def _write_report_merge2_noborder_bold(self, val, col1, col2):
        self.sheet.merge_range(
            self.row_pos, col1, self.row_pos, col2,_('')+val+_(''), self.format_title_noborder_bold)
        
    def convert_date_content(self, date):
        if date:
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%d-%m-%Y')
        return ''
    
    def get_product_name(self, objects, export=False):
        name = ''
        if export:
            if objects.selected:
                for prod in objects.product_ids:
                    if prod in objects.license_ids.export_item_id:
                        if name:
                            name += ", "+prod.name
                        else:
                            name += prod.name
            else:
                for prod in objects.license_ids.export_item_id:
                    if name:
                        name += ", "+prod.name
                    else:
                        name += prod.name
            if name:
                desc = objects.license_ids.export_desc or ' '
                name += ' '+desc
        else:
            if objects.selected:
                for prod in objects.product_ids:
                    if prod in objects.license_ids.import_item_id:
                        if name:
                            name += ", "+prod.name
                        else:
                            name += prod.name
            else:
                for prod in objects.license_ids.import_item_id:
                    if name:
                        name += ", "+prod.name
                    else:
                        name += prod.name
            if name:
                desc = objects.license_ids.import_desc or ' '
                name += ' '+desc
        return name
        
#     def _set_dynamic_headers(self, workbook, objects=False):
#         column = 0        
#         self._write_report_mergerows_header('S.No', self.row_pos, self.row_pos+1, column)
#         self.sheet.set_column(column, column, 6)
#         column += 1
#         self._write_report_mergecols_header('Incoming Details', column, column+2)
#         column += 3
#         self._write_report_mergecols_header('Outgoing Details', column, column+2)
#         column += 3
#         self._write_report_mergecols_header('Main Product Details', column, column+1)
#         column += 2
#         self._write_report_mergecols_header('Sub Product Details', column, column+5)
#         
#         self.row_pos += 1
#         column = 1
#         self.sheet.write_string(self.row_pos, column, _('Supplier Name'), self.format_header)
#         self.sheet.set_column(column, column, 22)
#         column += 1
#         self.sheet.write_string(self.row_pos, column, _('In Date'), self.format_header)
#         self.sheet.set_column(column, column, 10)
#         column += 1  
# #         self.sheet.write_string(self.row_pos, column, _('Bill No'), self.format_header)
# #         self.sheet.set_column(column, column, 15)
# #         column += 1
#         self.sheet.write_string(self.row_pos, column, _('Inward No'), self.format_header)
#         self.sheet.set_column(column, column, 15)
#         column += 1
#         self.sheet.write_string(self.row_pos, column, _('Customer Name'), self.format_header)
#         self.sheet.set_column(column, column, 22)
#         column += 1         
#         self.sheet.write_string(self.row_pos, column, _('Out Date'), self.format_header)
#         self.sheet.set_column(column, column, 10)
#         column += 1  
#         self.sheet.write_string(self.row_pos, column, _('Outward No'), self.format_header)
#         self.sheet.set_column(column, column, 15)
#         column += 1 
#         self.sheet.write_string(self.row_pos, column, _('Product Name'), self.format_header)
#         self.sheet.set_column(column, column, 19)
#         column += 1 
#         self.sheet.write_string(self.row_pos, column, _('Product Qty'), self.format_header)
#         self.sheet.set_column(column, column, 19)
#         column += 1
#         self.sheet.write_string(self.row_pos, column, _('Product Name'), self.format_header)
#         self.sheet.set_column(column, column, 16)
#         column += 1   
#         self.sheet.write_string(self.row_pos, column, _('Reference'), self.format_header)
#         self.sheet.set_column(column, column, 22)
#         column += 1
#         self.sheet.write_string(self.row_pos, column, _('Inward QTY'), self.format_header)
#         self.sheet.set_column(column, column, 16)
#         column += 1
#         self.sheet.write_string(self.row_pos, column, _('Outward QTY'), self.format_header)
#         self.sheet.set_column(column, column, 16)
#         column += 1
#         self.sheet.write_string(self.row_pos, column, _('Balance QTY'), self.format_header)
#         self.sheet.set_column(column, column, 16)
# #         column += 1
# #         self.sheet.write_string(self.row_pos, column, _('Stock Value'), self.format_header)
# #         self.sheet.set_column(column, column, 16)
#         
# #         self.sheet.freeze_panes(10, 0)
#         self.row_pos += 1  
        
    def _set_dynamic_headers(self, workbook, objects=False):
        column = 0        
        self.sheet.write_string(self.row_pos, column, _('S.No'), self.format_header)
        self.sheet.set_column(column, column, 6)
        column += 1
        self.sheet.write_string(self.row_pos, column, _('In/Out Date'), self.format_header)
        self.sheet.set_column(column, column, 14)
        column += 1          
        self.sheet.write_string(self.row_pos, column, _('Supplier/Customer Name'), self.format_header)
        self.sheet.set_column(column, column, 30)
        column += 1     
        self.sheet.write_string(self.row_pos, column, _('Supplier/Customer Inv No'), self.format_header)
        self.sheet.set_column(column, column, 30)
        column += 1    
        self.sheet.write_string(self.row_pos, column, _('Tracking ID'), self.format_header)
        self.sheet.set_column(column, column, 22)
        column += 1 
        self.sheet.write_string(self.row_pos, column, _('Main Product'), self.format_header)
        self.sheet.set_column(column, column, 25)
        column += 1 
        self.sheet.write_string(self.row_pos, column, _('Main Product qty'), self.format_header)
        self.sheet.set_column(column, column, 19)
        column += 1 
        self.sheet.write_string(self.row_pos, column, _('Sub Product'), self.format_header)
        self.sheet.set_column(column, column, 25)
        column += 1   
        self.sheet.write_string(self.row_pos, column, _('Sub Product IN Qty'), self.format_header)
        self.sheet.set_column(column, column, 22)
        column += 1
        self.sheet.write_string(self.row_pos, column, _('Unit Price'), self.format_header)
        self.sheet.set_column(column, column, 15)
        column += 1
        self.sheet.write_string(self.row_pos, column, _('In Value'), self.format_header)
        self.sheet.set_column(column, column, 15)
        column += 1        
        self.sheet.write_string(self.row_pos, column, _('Sub Product OUT Qty'), self.format_header)
        self.sheet.set_column(column, column, 26)
        column += 1
        self.sheet.write_string(self.row_pos, column, _('Unit Price'), self.format_header)
        self.sheet.set_column(column, column, 15)
        column += 1
        self.sheet.write_string(self.row_pos, column, _('Out Value'), self.format_header)
        self.sheet.set_column(column, column, 15)
        column += 1
        self.sheet.write_string(self.row_pos, column, _('Balance QTY'), self.format_header)
        self.sheet.set_column(column, column, 16)
        column += 1
        self.sheet.write_string(self.row_pos, column, _('AVG Cost'), self.format_header)
        self.sheet.set_column(column, column, 15)
        column += 1
        self.sheet.write_string(self.row_pos, column, _('Value'), self.format_header)
        self.sheet.set_column(column, column, 15)
        
#         self.sheet.freeze_panes(10, 0)
        self.row_pos += 1  
        
#     def _generate_report_content(self, objects):
#         if objects:     
#             res = objects.get_result()
#             sino = balance = tot_inward = tot_outward = 0
#             bill_dict = {}
#             for line in res:
#                 column = 0
#                 
#                 if line.get('grn_no', False) in bill_dict:
#                     del line['main_prod_name']
#                     del line['bill_date']
#                     del line['grn_no']
#                     del line['supplier']
#                     del line['qty']
#                     #del line['customer']
#                 elif not line.get('grn_no', False) in bill_dict:
#                     sino += 1
#                     bill_dict[line['grn_no']] = line['supplier']
#                 elif not line.get('supplier', False) in bill_dict:
#                     bill_dict[line['supplier']] = line['supplier']
#                 elif not line.get('qty', False) in bill_dict:
#                     bill_dict[line['qty']] = line['qty']
#                 #------------ elif not line.get('customer', False) in bill_dict:
#                     #------------ bill_dict[line['customer']] = line['customer']
#                     
#                 balance = line['inward'] - line['outward']
#                 tot_inward += line['inward']
#                 tot_outward += line['outward']
#                 ref_name = line.get('ref_name','')
#                 try:
#                     ref_name = line.get('ref_name','') +"-"+line.get('ref_name1','')
#                 except:
#                     pass
#                 if line.get('grn_no',''):
#                     self.sheet.write_number(self.row_pos, column, sino, self.format_title)   
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(line.get('supplier','')), self.format_title)
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(self.convert_date_content(line.get('bill_date',''))), self.format_title)
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(line.get('grn_no','')), self.format_title)
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(line.get('customer','')), self.format_title)
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(self.convert_date_content(line.get('out_date',''))), self.format_title)
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(line.get('do_no','')), self.format_title)
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(line.get('main_prod_name','')), self.format_title)
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(line.get('qty','')), self.format_title)
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(line.get('product_name','')), self.format_title)
#                 column += 1
#                 self.sheet.write_string(self.row_pos, column, _(ref_name), self.format_title)
#                 column += 1
#                 self.sheet.write_number(self.row_pos, column, line.get('inward',0), self.format_title_number) 
#                 column += 1
#                 self.sheet.write_number(self.row_pos, column, line.get('outward',0), self.format_title_number) 
#                 column += 1
#                 self.sheet.write_number(self.row_pos, column, balance, self.format_title_number) 
#                 column += 1
#                    
#                 self.row_pos +=1
#             ## total line update
#             column = 0
#             self.sheet.write_number(self.row_pos, column, sino+1, self.format_title)   
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
#             column += 1
#             self.sheet.write_string(self.row_pos, column, _('Total'), self.format_header)
#             column += 1
#             self.sheet.write_number(self.row_pos, column, tot_inward, self.format_title_number_bold) 
#             column += 1
#             self.sheet.write_number(self.row_pos, column, tot_outward, self.format_title_number_bold) 
#             column += 1
#             self.sheet.write_number(self.row_pos, column, tot_inward-tot_outward, self.format_title_number_bold) 
#             column += 1

    def _generate_report_content(self, objects):
        if objects:     
            res = objects.get_result()
            sino = balance = tot_inward = tot_outward = in_sub_total = out_sub_total = 0
            product_dict = {}
            remove_dup_main_prod = {}
            remove_dup_data = {}
            for line in res:   
                column = 0  
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
                        del line['in_out_date']
                        del line['partner']
                        del line['inv_no']
                        del line['main_prod_name']
                        del line['main_prod_qty']
                        del line['ref']
                        
                    elif not line.get('transfer_id') in remove_dup_main_prod:
                        remove_dup_main_prod[line['transfer_id']] = line.get('transfer_id')
                        sino += 1
                        self.sheet.write_number(self.row_pos, column, sino, self.format_title)   
                
                if line.get('pick_id', False) and (line.get('outward',False) or line.get('inward',False)):
                    if line.get('pick_id') in remove_dup_data:
                        del line['in_out_date']
                        del line['partner']
                        del line['inv_no']
                        del line['main_prod_name']
                        del line['main_prod_qty']
                        
                    elif not line.get('pick_id') in remove_dup_data:
                        remove_dup_data[line['pick_id']] = line.get('pick_id')
                        sino += 1
                        self.sheet.write_number(self.row_pos, column, sino, self.format_title) 
                        
                column += 1                
                balance = product_dict[line['sub_prod_id']]        
                
                self.sheet.write_string(self.row_pos, column, _(self.convert_date_content(line.get('in_out_date',''))), self.format_title)
                column += 1
                self.sheet.write_string(self.row_pos, column, _(line.get('partner','')), self.format_title)
                column += 1
                self.sheet.write_string(self.row_pos, column, _(line.get('inv_no','')), self.format_title)
                column += 1     
                self.sheet.write_string(self.row_pos, column, _(line.get('ref','')), self.format_title)
                column += 1             
                self.sheet.write_string(self.row_pos, column, _(line.get('main_prod_name','')), self.format_title)
                column += 1
                self.sheet.write_number(self.row_pos, column, line.get('main_prod_qty',0), self.format_title_number) 
                column += 1
                self.sheet.write_string(self.row_pos, column, _(line.get('sub_prod_name','')), self.format_title)
                column += 1
                self.sheet.write_number(self.row_pos, column, in_qty, self.format_title_number) 
                column += 1                
                self.sheet.write_number(self.row_pos, column, line.get('in_price_unit',0), self.format_title_number) 
                column += 1
                self.sheet.write_number(self.row_pos, column, line.get('in_subtotal',0), self.format_title_number) 
                column += 1
                self.sheet.write_number(self.row_pos, column, out_qty, self.format_title_number) 
                column += 1
                self.sheet.write_number(self.row_pos, column, line.get('out_price_unit',0), self.format_title_number) 
                column += 1
                self.sheet.write_number(self.row_pos, column, line.get('out_subtotal',0), self.format_title_number) 
                column += 1
                self.sheet.write_number(self.row_pos, column, balance, self.format_title_number) 
                column += 1
                self.sheet.write_number(self.row_pos, column, 0, self.format_title_number) 
                column += 1
                self.sheet.write_number(self.row_pos, column, 0, self.format_title_number) 
                column += 1
                   
                self.row_pos +=1
                
                tot_inward += in_qty
                in_sub_total += line.get('in_subtotal',0)
                
                tot_outward += out_qty
                out_sub_total += line.get('out_subtotal',0)
                
            ## total line update
            column = 0
            self.sheet.write_number(self.row_pos, column, sino+1, self.format_title)   
            column += 1
            self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
            column += 1
            self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
            column += 1
            self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
            column += 1
            self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
            column += 1
            self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
            column += 1
            self.sheet.write_string(self.row_pos, column, _(''), self.format_title)
            column += 1
            self.sheet.write_string(self.row_pos, column, _('Total'), self.format_header)
            column += 1
            self.sheet.write_number(self.row_pos, column, tot_inward, self.format_title_number_bold) 
            column += 1
            
            cost = 0
            if tot_inward < 0 or tot_inward > 0:
                cost = in_sub_total/tot_inward
            self.sheet.write_number(self.row_pos, column, cost, self.format_title_number_bold) 
            column += 1
            self.sheet.write_number(self.row_pos, column, in_sub_total, self.format_title_number_bold) 
            column += 1
            self.sheet.write_number(self.row_pos, column, tot_outward, self.format_title_number_bold) 
            column += 1
            cost = 0
            if tot_outward < 0 or tot_outward > 0:
                cost = out_sub_total/tot_outward
            self.sheet.write_number(self.row_pos, column, cost, self.format_title_number_bold) 
            column += 1
            self.sheet.write_number(self.row_pos, column, out_sub_total, self.format_title_number_bold) 
            column += 1
            self.sheet.write_number(self.row_pos, column, tot_inward-tot_outward, self.format_title_number_bold) 
            column += 1
            cost = 0
            if (tot_inward-tot_outward) < 0 or (tot_inward-tot_outward) > 0:
                cost = abs((in_sub_total-out_sub_total)/(tot_inward-tot_outward))
            self.sheet.write_number(self.row_pos, column, cost, self.format_title_number_bold) 
            column += 1
            self.sheet.write_number(self.row_pos, column, in_sub_total-out_sub_total, self.format_title_number_bold) 
            column += 1
            
            
    def generate_xlsx_report(self, workbook, data, objects):
        # Initial row
        self.row_pos = 0

        # Load formats to workbook
        self._define_formats(workbook)
        org_name = ' '
        # Set report name
        report_name = "Stock Journal Report"
        sheet_name=report_name
        self.sheet = workbook.add_worksheet(sheet_name)
        if data.get('landscape'):
            self.sheet.set_landscape()
        self.sheet.fit_to_pages(1, 0)
        self.sheet.set_zoom(80)
        
        self.row_pos += 1
        self._write_report_subtitle_bold_background(report_name)     
        self._write_report_subtitle_bold(objects.company_id.name)
        
        if objects.org_id:
            org_name = objects.org_id.name
        else:
            for org in self.env['res.company'].search([('parent_id','=',objects.company_id.id)]):
                org_name += org.name +" , "
        
        ##company_address
        company_address = ''
        if objects.company_id.street:
            company_address += objects.company_id.street or ''
        if objects.company_id.street2:
            company_address += ", "+objects.company_id.street2 or ''
        if objects.company_id.city:
            company_address += ", "+objects.company_id.city or ''
        if objects.company_id.state_id:
            company_address += ", "+objects.company_id.state_id.name or ''
        if objects.company_id.zip:
            company_address += " - "+objects.company_id.zip or ''
        if objects.company_id.country_id:
            company_address += ", "+objects.company_id.country_id.name or ''
         
        self._write_report_subtitle(company_address)
        self.row_pos += 1
        column = 0
        self._write_report_mergecols('Organization', column, column+1)
        column += 2
        self._write_report_mergecols(org_name, column, column+2)
        column += 4
        self.sheet.write_string(self.row_pos, column, _('Date From'), self.format_title)  
        self.sheet.set_column(column, column, 10)      
        column += 1
        self.sheet.write_string(self.row_pos, column, _(self.convert_date_content(objects.date_from)), self.format_title)
        self.sheet.set_column(column, column, 10)
        column += 2
        self.sheet.write_string(self.row_pos, column, _('Date to'), self.format_title)      
        self.sheet.set_column(column, column, 10)
        column += 1  
        self.sheet.write_string(self.row_pos, column, _(self.convert_date_content(objects.date_to)), self.format_title)
        self.sheet.set_column(column, column, 10)
        
        self.row_pos += 2       
        
        # Set headers
        self._set_dynamic_headers(workbook, objects=objects)
        self._generate_report_content(objects)


if ReportXlsx != object:
    StockJournalReportXlsx(
        'report.stock_transfer.stock_journal_report_xls',
        'stock.journal.report', parser=report_sxw.rml_parse
    )
