# -*- coding: utf-8 -*-

from datetime import datetime
from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.osv import osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import float_compare, float_is_zero
from openerp.tools.translate import _
from openerp import tools, SUPERUSER_ID
from openerp.exceptions import UserError, AccessError
import openerp.addons.decimal_precision as dp

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    stock_transfer_done = fields.Boolean(string='Transfer Done', default=False)
    
class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    stock_transfer_done = fields.Boolean(string='Transfer Done', default=False)

class StockTransferSettings(models.Model):
    _name = 'stock.transfer.settings'
    _description = 'Stock Transfer Settings'
    
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id.id, required=True)
    diff_amount = fields.Boolean(string="Validation for Difference Amount",default=False, help="Validation Controls for Difference Amount (Consumable products total amount and products to Produce total amount)")
    diff_qty = fields.Boolean(string="Validation for Difference Quantity",default=False, help="Validation Controls for Difference Quantity (Consumable products total Quantity and products to Produce total Quantity)")
    same_product = fields.Boolean(string="Validation for Different Products",default=False, help="Validation Controls for Different products from invoice (Consumable products and invoice products)")
    only_single_product = fields.Boolean(string="Only Single Consumable Product",default=False, help="Validation Controls for Consumable products (Consumable products must be single line)")
    alert_stock = fields.Boolean(string="Product Stock Not available Alert",default=False, help="Validation Controls for Stock not available products (Consumable products stock checking alert message if not stock)")
    invoice_diff_qty = fields.Boolean(string="Validation for Invoice Quantity",default=False, help="Validation Controls if Quantity exceeds more than invoiced (Consumable products quantity should not exceed invoice quantity)")
    
    @api.multi
    @api.constrains('company_id')
    def _check_multi_records(self):
        for rec in self:
            if self.search([('company_id','=',rec.company_id.id),('id','!=',rec.id)]):
                raise UserError(_('Configuration Must be Unique for Company'))
            
class StockTransfer(models.Model):
    """
    Stock Transfer
    """
    _name = 'stock.transfer'
    _description = 'Stock Transfer'
    _order = 'name desc, date'

    @api.multi
    @api.onchange('state')
    def test_trigger(self):
        self._check_approval_controls()
        
    @api.multi
    def _check_approval_controls(self):
        for record in self:
            amt_control = qty_control = product_control = single_product_validation = alert_stock = invoice_diff_qty = False
            settings = self.env['stock.transfer.settings'].search([('company_id','=',self.env.user.company_id.id)])
            if settings:
                amt_control = settings.diff_amount
                qty_control = settings.diff_qty
                product_control = settings.same_product
                single_product_validation = settings.only_single_product
                alert_stock = settings.alert_stock
                invoice_diff_qty = settings.invoice_diff_qty
            record.update({
                          'diff_amount_validation': amt_control,
                          'diff_qty_validation': qty_control,
                          'product_validation': product_control,
                          'single_product_validation': single_product_validation,
                          'alert_stock': alert_stock,
                          'invoice_diff_qty': invoice_diff_qty,
                          })
        
    name = fields.Char('Name', required=True, copy=False, readonly=True, default="New")
    company_id = fields.Many2one('res.company', string="Company", ondelete="restrict", default=lambda self: self.env.user.company_id, required=True)
    org_id = fields.Many2one('res.company', string="Organization", ondelete="restrict")
    location_id = fields.Many2one('stock.location', 'Stock Location', ondelete="restrict", required=True, readonly=True, states={'draft': [('readonly', False)]}, help="Location where the system will look for components.")
    date = fields.Date(sting="Date", default=fields.Datetime.now, copy=False)
    note = fields.Text(string="Description")
    diff_amount = fields.Float(string="Difference Amount", default=0.0, help="Is The Consumable total and Producible total Value mismatch then give this value, it will add on producible side")
    diff_qty = fields.Float(string="Difference Quantity", default=0.0, help="Is The Consumable total and Producible total Quantity mismatch then give use this, it will add on producible side")
    diff_amount_validation = fields.Boolean(string="Amount Validation", compute='_check_approval_controls')
    diff_qty_validation = fields.Boolean(string="Quantity Validation", compute='_check_approval_controls')
    product_validation = fields.Boolean(string="Product Validation", compute='_check_approval_controls')
    alert_stock = fields.Boolean(string="Alert", compute='_check_approval_controls')
    invoice_diff_qty = fields.Boolean(string="Inv Qty Control", compute='_check_approval_controls')
    single_product_validation = fields.Boolean(string="Products Count Validation", compute='_check_approval_controls')
    state = fields.Selection([('draft', 'New'), ('partially_available', 'Partially Available'),('available', 'Ready to Produce'), 
                              ('done', 'Done'), ('cancel', 'Cancelled')],
                             string="Status", default="draft")
    invoice_id = fields.Many2one('account.invoice', string="Bill Number", ondelete="restrict", copy=False)
    partner_id = fields.Many2one('res.partner', string="Partner Id", ondelete="restrict", copy=False)
    partner_name = fields.Char(string='Partner Name', related="partner_id.name")
    stock_transfer_done = fields.Boolean(string="Invoice Btn Control", default=False)
    input_product_lines = fields.One2many('stock.transfer.product.line', 'input_transfer_id', 'Input Products', copy=True)
    output_product_lines = fields.One2many('stock.transfer.product.line', 'output_transfer_id', 'Output Products', copy=True)
    input_move_lines = fields.One2many('stock.move', 'input_transfer_id', 'Input Products', copy=False)
    output_move_lines = fields.One2many('stock.move', 'output_transfer_id', 'Output Products', copy=False)
    # ~ reference_id = fields.Many2one('reference.master', string="Tracking ID", ondelete="restrict", store=True, copy=False)
    picking_ids = fields.Many2many('stock.picking','stock_transfer_picking_rel','transfer_id','picking_id', string="GRN/MRN")
    inv_no = fields.Char('Inv No', copy=False)
    
    # ~ @api.multi
    # ~ @api.constrains('org_id','location_id')
    # ~ def _check_location_org(self):
        # ~ for rec in self:
            # ~ if rec.org_id and rec.location_id:
                # ~ if rec.location_id.company_id != rec.org_id:
                    # ~ print (rec.location_id.company_id,rec.org_id)
                    # ~ raise UserError(_('Organization is Mismatch with location Organization'))
                
    # ~ @api.multi
    # ~ @api.constrains('company_id','location_id')
    # ~ def _check_location_company(self):
        # ~ for rec in self:
            # ~ if rec.company_id and rec.location_id:
                # ~ if rec.location_id.company_id != rec.company_id:
                    # ~ print (rec.location_id.company_id,rec.org_id,rec.company_id,)
                    # ~ raise UserError(_('Company is Mismatch with location Company'))
    @api.multi
    @api.onchange('org_id')
    def onchange_org_id(self):
        if self.org_id:
            loc_ids = self.env['stock.location'].search([('company_id','=',self.org_id.id),('usage','=','internal')])
            if not loc_ids:
                raise UserError(_('Please map at least one location to selected organization\nLocation and Organization mapping is missing'))
            self.location_id = min(loc_ids) and min(loc_ids).id or False
            
#     @api.multi
#     @api.onchange('invoice_id')
#     def onchange_invoice_id(self):
#         if self.invoice_id:
#             new_lines = self.env['stock.transfer.product.line']
#             for ln in self.input_product_lines:
#                 self.input_product_lines -= ln
#             for line in self.invoice_id.invoice_line_ids:
#                 data = self._prepare_input_line(line)
#                 new_line = new_lines.new(data)
#                 new_lines += new_line
#             self.input_product_lines += new_lines
#             self.partner_name = self.invoice_id.partner_id.name
#             self.partner_id = self.invoice_id.partner_id and self.invoice_id.partner_id.id or False
            
    @api.multi
    @api.onchange('picking_ids')
    def onchange_picking_ids(self):
        if self.picking_ids:
            if len(self.picking_ids.mapped('partner_id')) > 1:
                raise UserError(_('Partner is not matching for recently selected GRN/MRN'))
            new_lines = self.env['stock.transfer.product.line']
            for ln in self.input_product_lines:
                if ln.picking_id not in self.picking_ids:
                    self.input_product_lines -= ln
            for pick in self.picking_ids-self.input_product_lines.mapped('picking_id'): 
                for move in pick.move_lines:
                    data = self._prepare_input_line(move)
                    new_line = new_lines.new(data)
                    new_lines += new_line
            self.input_product_lines += new_lines
            self.partner_name = max(self.picking_ids).partner_id.name or ''
            self.inv_no = max(self.picking_ids).origin or ''
            self.partner_id = max(self.picking_ids).partner_id and max(self.picking_ids).partner_id.id or False
        else:
            self.partner_id = False
            
            
    def _prepare_input_line(self, line):
        data = {}
        if line:
            data['product_id'] = line.product_id and line.product_id.id or False
            data['product_qty'] = line.product_qty
            data['product_uom'] = line.product_uom and line.product_uom.id or False
            data['price_unit'] = line.price_unit
            data['name'] = line.name or '/'
            data['currency_id'] = line.company_id.currency_id.id or False
            data['picking_id'] = line.picking_id and line.picking_id.id or False
        return data
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.transfer') or 'New'
        return super(StockTransfer, self).create(vals)
    
    @api.multi
    def get_property_stock_inventory(self):
        loc = False
        locs = self.env['stock.location'].search([('usage','=','inventory'),('scrap_location','=',False)], order="id desc", limit=1)
        if locs:
            loc = locs.id
        return loc
    
    @api.multi
    def prepare_move_vals(self, line):
        input_transfer_id = output_transfer_id = location_id = location_dest_id = picking_type_id = False
        loc_id = line.product_id.property_stock_inventory and line.product_id.property_stock_inventory.id or False
        if not loc_id:
            loc_id = self.get_property_stock_inventory()
        if line.input_transfer_id:
            input_transfer_id = self.id
            location_id = self.location_id and self.location_id.id or False
            location_dest_id = loc_id
        elif line.output_transfer_id:
            output_transfer_id = self.id
            location_dest_id = self.location_id and self.location_id.id or False
            location_id = loc_id
        rec_date = str(self.date)+" "+str(datetime.now())[11:]
        move_vals = {
                    'product_id' : line.product_id.id,
                    'product_uom_qty' : line.product_qty or 0,
                    'product_uom' : line.product_uom and line.product_uom.id or False,
                    'location_id' : location_id,
                    'location_dest_id' : location_dest_id,
                    'name' : line.product_id.name,
                    'picking_id' : False,
                    'picking_type_id' : picking_type_id,
                    'company_id': self.company_id and self.company_id.id or False,
                    'org_id': self.org_id and self.org_id.id or False,
                    'price_unit': line.price_unit,
                    'input_transfer_id': input_transfer_id,
                    'output_transfer_id': output_transfer_id,
                    'date': rec_date,
                    'date_expected': rec_date,
                    'origin': self.name,
                }
        return move_vals
        
    @api.multi
    def check_validations(self):
        rec = self
        consume_total_value = produce_total_value = consume_total_qty = produce_total_qty = 0
        for inline in rec.input_product_lines:
            consume_total_value += inline.price_subtotal
            consume_total_qty += inline.product_qty
        for outline in rec.output_product_lines:
            produce_total_value += outline.price_subtotal
            produce_total_qty += outline.product_qty
        if not consume_total_value or not produce_total_value:
            raise UserError(_('The Total value should not 0 (Zero)'))
        
        if rec.diff_amount_validation:
            if consume_total_value != (produce_total_value+rec.diff_amount):
                raise UserError(_('The Total Consumable value and Total Producible value must be same'))
        if rec.diff_qty_validation:
            if consume_total_qty != (produce_total_qty+rec.diff_qty):
                raise UserError(_('The Total Consumable Quantity and Total Producible Quantity must be Equal'))
        if rec.single_product_validation:
            if len(rec.input_product_lines) > 1:
                raise UserError(_('Consumable products are allowed only One\nPlease Remove some consumable products'))
        
        
        if rec.product_validation and rec.picking_ids:
            rec_product_ids  = rec.input_product_lines.mapped('product_id')
            inv_product_ids = rec.input_product_lines.mapped('picking_id').mapped('move_lines').mapped('product_id')
            for prod in rec_product_ids:
                if prod not in inv_product_ids:
                    raise UserError(_('GRN/MRN Related products and Consumable products are not matching\nPlease check the products on selected GRN/MRN'))
#         if rec.invoice_diff_qty and rec.picking_ids:
#             inv_line_dict = {}
#             for inline in rec.input_product_lines:
#                 if inline.invoice_line_id:
#                     if inline.invoice_line_id.id in inv_line_dict:
#                         inv_line_dict[inline.invoice_line_id.id] = inv_line_dict[inline.invoice_line_id.id]+inline.product_qty
#                     else:
#                         inv_line_dict[inline.invoice_line_id.id] = inline.product_qty
#                     for other_lines in self.env['stock.transfer.product.line'].search([('invoice_line_id','=',inline.invoice_line_id.id),('id','!=',inline.id)]):
#                         inv_line_dict[inline.invoice_line_id.id] = inv_line_dict[inline.invoice_line_id.id]+other_lines.product_qty 
#             for ln in rec.invoice_id.invoice_line_ids:
#                 if inv_line_dict.get(ln.id, False):
#                     if inv_line_dict[ln.id] > ln.quantity:
#                         raise UserError(_('Bill Related products Quantity and Consumable products quantity not matching\nYou are Exceeded Invoiced Quantity'))
    @api.multi
    def action_confirm(self):
        for rec in self:
            for ln in rec.input_move_lines+rec.output_move_lines:
                ln.sudo().unlink()
            if not rec.input_product_lines or not rec.output_product_lines:
                raise UserError(_('Some Consumable or Producible product lines are mandatory'))
            if rec.state != 'draft':
                raise UserError(_('You can confirm only New State Records'))
            rec.check_validations()
            for input_line in rec.input_product_lines+rec.output_product_lines:
                move_vals = rec.prepare_move_vals(input_line)
                move_id = self.env['stock.move'].create(move_vals)
                move_id._action_confirm()
                move_id._action_assign()                
            
            partial_available_states = []
            available_states = []
            for mvline in rec.input_move_lines:
                if mvline.state == 'partially_available':
                    partial_available_states.append(mvline)
                elif mvline.state == 'assigned':
                    available_states.append(mvline)
            if any(partial_available_states) and len(partial_available_states) > 0:
                rec.state = 'partially_available'
            elif any(available_states) and len(available_states) == len(rec.input_product_lines):
                rec.state = 'available'
            if rec.state == 'draft':
                raise UserError(_('Stock Not available for selected products'))
        return True
                
    @api.multi
    def action_done(self):
        for rec in self:
            if rec.state != 'available':
                raise UserError(_('You can Transfer only Available State Records'))
            for mvl in rec.input_move_lines+rec.output_move_lines:
                mvl._action_done()
                # ~ mvl.date = str(rec.date)+" "+str(datetime.now())[11:]
                # ~ mvl.update_stock_quant_date()
            rec.state = 'done'
            # ~ if rec.sudo().reference_id:
                # ~ rec.reference_id.sudo().state = 'available'
                # ~ rec.reference_id.sudo().product_ids += rec.output_move_lines.mapped('product_id')
                # ~ rec.reference_id.sudo().product_ids += rec.input_move_lines.mapped('product_id')
        return True
    
    @api.multi
    def action_update_pickings_done(self):
        for rec in self:
            if rec.picking_ids:
                for pick in rec.picking_ids:
                    pick.sudo().write({'stock_transfer_done':True})
                rec.stock_transfer_done = True
                
    @api.multi
    def action_update_pickings_available(self):
        for rec in self:
            if rec.picking_ids:
                for pick in rec.picking_ids:
                    pick.sudo().write({'stock_transfer_done':False})
                rec.stock_transfer_done = False
    
    @api.multi
    def action_cancel(self):
        for rec in self:
            for line in rec.output_move_lines+rec.input_move_lines:
                # ~ line.update_product_average_cost(cancel=True)
                # ~ line.quant_cancel_from_move()
                line.state = 'assigned'
                line._action_cancel()
            rec.state = 'cancel'
            # ~ if rec.sudo().reference_id and rec.reference_id.sudo().state == 'available':
                # ~ rec.reference_id.sudo().state = 'draft'
                # ~ rec.reference_id.sudo().product_ids -= rec.output_move_lines.mapped('product_id')
                # ~ rec.reference_id.sudo().product_ids -= rec.input_move_lines.mapped('product_id')
        return True
    
    @api.multi
    def action_draft(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('You can Set as New only Cancel State Records'))
            for mvl in rec.input_move_lines+rec.output_move_lines:
                mvl._action_set_draft()
            rec.state = 'draft'
        return True
            
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You can delete only New State Records'))
        return super(StockTransfer, self).unlink()
    
class StockMove(models.Model):
    _inherit = 'stock.move'
    
    input_transfer_id = fields.Many2one('stock.transfer', string='Input Stock Transfer', ondelete="set null")
    output_transfer_id = fields.Many2one('stock.transfer', string='Output Stock Transfer', ondelete="set null")
    # ~ reference_id = fields.Many2one('reference.master', string="Tracking ID", ondelete="restrict")
    
# ~ class StockPackOperation(models.Model):
    # ~ _inherit = 'stock.pack.operation'
    
    # ~ reference_ids = fields.Many2many('reference.master', string="Tracking ID", ondelete="restrict")
    
    # ~ def create(self, cr, user, vals, context=None):        
        # ~ picking_id = vals.get('picking_id')
        # ~ product_id = vals.get('product_id')
        # ~ uid = user
        # ~ if picking_id:
            # ~ st_move = self.pool.get('stock.move').search(cr, uid, [('picking_id','=',picking_id),('product_id','=',product_id)], context=context)
            # ~ if st_move:
                # ~ st = self.pool['stock.move'].browse(cr, uid, st_move, context=context)
                # ~ reference_ids = []
                # ~ for st_line in st:
                    # ~ if st_line.reference_id:
                        # ~ reference_ids.append(st_line.reference_id.id)
                # ~ vals.update({'reference_ids': [(6, 0, reference_ids)]})
        # ~ return super(StockPackOperation, self).create(cr, user, vals, context)
    
class StockTransferProductLine(models.Model):
    _name = 'stock.transfer.product.line'
    _description = 'Transfer Product Lines'
    _order = 'id desc'
    
    @api.depends('product_qty','price_unit')
    def _compute_amount(self):
        for line in self:
            price_subtotal = line.product_qty * line.price_unit
            line.update({
                         'price_subtotal': price_subtotal
                         })
    
    input_transfer_id = fields.Many2one('stock.transfer', string="Input Stock Transfer", ondelete="cascade", copy=False)
    output_transfer_id = fields.Many2one('stock.transfer', string="Output Stock Transfer", ondelete="cascade", copy=False)
    product_id = fields.Many2one('product.product', string='Product', required=True, ondelete="restrict")
    product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    qty_available = fields.Float(string="QTY Available", related="product_id.qty_available", readonly=True)
    uom_id = fields.Many2one('product.uom', 'Unit of Measure')
    name = fields.Char(string='Deacription',required=True, copy=False, default="New")
    price_unit = fields.Float('Rate')
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.user.company_id.currency_id)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Total', readonly=True)
    invoice_line_id = fields.Many2one('account.invoice.line', string="Invoice Line", copy=False, ondelete="restrict")
    picking_id = fields.Many2one('stock.picking', string="Picking", copy=False, ondelete="restrict")
    
    @api.multi
    @api.constrains('price_unit')
    def _check_price_unit(self):
        for line in self:
            if line.price_unit < 0:
                raise UserError(_('Negative Unit Price not allowed'))
            
    @api.multi
    @api.constrains('product_qty')
    def _check_product_qty(self):
        for line in self:
            if line.product_qty < 0:
                raise UserError(_('Negative Quantity not allowed'))
    @api.multi
    def get_validation_message(self):
        if self.product_id.type == 'product' and self.product_id.qty_available < 0.1:
            warning_mess = {
                'title': _('Quantity Not Available!'),
                'message' : _('The stock not available for the selected product .'),
            }
            return {'warning': warning_mess}
        if self.product_id.type == 'product' and self.product_id.qty_available < self.product_qty:
            warning_mess = {
                'title': _('Not Enough Quantity!'),
                'message' : _('You Entered more than available Quantity.'),
            }
            return {'warning': warning_mess}
        return {}
            
    @api.onchange('product_qty')
    def _onchange_product_qty_check_availability(self):
        if not self.product_id or not self.product_qty or not self.product_uom:
            return {}
        if self.input_transfer_id and self.input_transfer_id.alert_stock:
            return self.get_validation_message()

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.name = line.product_id.name
                line.product_uom = line.product_id.uom_id and line.product_id.uom_id.id or False
                line.uom_id = line.product_id.uom_id and line.product_id.uom_id.id or False
                if line.input_transfer_id and self.input_transfer_id.alert_stock:
                    return self.get_validation_message()
                
    @api.model
    def create(self, vals):
        prod = self.env['product.product'].browse(vals['product_id'])
        vals['uom_id'] = prod.uom_id.id
        vals['product_uom'] = vals['uom_id'] 
        return super(StockTransferProductLine, self).create(vals)
    
    @api.multi
    def write(self, vals):
        if 'uom_id' in vals:
            vals['product_uom'] = vals['uom_id']
        return super(StockTransferProductLine, self).write(vals)
    

