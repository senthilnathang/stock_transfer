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

    
class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    stock_transfer_done = fields.Boolean(string='Transfer Done', default=False)


class StockTransfer(models.Model):
    """
    Stock Transfer
    """
    _name = 'stock.transfer'
    _description = 'Stock Transfer'
    _order = 'name desc, date'

        
    name = fields.Char('Name', required=True, copy=False, readonly=True, default="New")
    company_id = fields.Many2one('res.company', string="Company", ondelete="restrict", default=lambda self: self.env.user.company_id, required=True)
    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit", ondelete="restrict")
    location_id = fields.Many2one('stock.location', 'Stock Location', ondelete="restrict", required=True, readonly=True, states={'draft': [('readonly', False)]}, help="Location where the system will look for components.")
    date = fields.Date(sting="Date", default=fields.Datetime.now, copy=False)
    note = fields.Text(string="Description")
    state = fields.Selection([('draft', 'New'), ('partially_available', 'Partially Available'),('available', 'Ready to Produce'), 
                              ('done', 'Done'), ('cancel', 'Cancelled')],
                             string="Status", default="draft")
    stock_transfer_done = fields.Boolean(string="Invoice Btn Control", default=False)
    input_product_lines = fields.One2many('stock.transfer.product.line', 'input_transfer_id', 'Input Products', copy=True)
    output_product_lines = fields.One2many('stock.transfer.product.line', 'output_transfer_id', 'Output Products', copy=True)
    input_move_lines = fields.One2many('stock.move', 'input_transfer_id', 'Input Products', copy=False)
    output_move_lines = fields.One2many('stock.move', 'output_transfer_id', 'Output Products', copy=False)
    
    # ~ @api.multi
    # ~ @api.constrains('operating_unit_id','location_id')
    # ~ def _check_location_org(self):
        # ~ for rec in self:
            # ~ if rec.operating_unit_id and rec.location_id:
                # ~ if rec.location_id.company_id != rec.operating_unit_id:
                    # ~ print (rec.location_id.company_id,rec.operating_unit_id)
                    # ~ raise UserError(_('Organization is Mismatch with location Organization'))
                
    # ~ @api.multi
    # ~ @api.constrains('company_id','location_id')
    # ~ def _check_location_company(self):
        # ~ for rec in self:
            # ~ if rec.company_id and rec.location_id:
                # ~ if rec.location_id.company_id != rec.company_id:
                    # ~ print (rec.location_id.company_id,rec.operating_unit_id,rec.company_id,)
                    # ~ raise UserError(_('Company is Mismatch with location Company'))
    @api.multi
    @api.onchange('operating_unit_id')
    def onchange_operating_unit_id(self):
        if self.operating_unit_id:
            loc_ids = self.env['stock.location'].search([('company_id','=',self.operating_unit_id.company_id.id),('usage','=','internal')])
            if not loc_ids:
                raise UserError(_('Please map at least one location to selected organization\nLocation and Organization mapping is missing'))
            self.location_id = min(loc_ids) and min(loc_ids).id or False
            
            
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
                    'operating_unit_id': self.operating_unit_id and self.operating_unit_id.id or False,
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
            rec.write({'state':'available'})
            # ~ if rec.state == 'draft':
                # ~ raise UserError(_('Stock Not available for selected products'))
        return True

    @api.multi
    def action_done(self):
        for rec in self:
            if rec.state != 'available':
                raise UserError(_('You can Transfer only Available State Records'))
            for mv,inp in zip((rec.input_move_lines+rec.output_move_lines),(rec.input_product_lines+rec.output_product_lines)):
                for move_line in mv.move_line_ids:
                    # ~ lot = self.env['stock.production.lot'].create(
                        # ~ {'name': move_line.lot_name, 'product_id': move_line.product_id.id}
                    # ~ )
                    move_line.write({'lot_id': inp.lot_id.id,'qty_done':mv.product_uom_qty})
                mv.move_line_ids._action_done()
                mv.write({'state': 'done', 'date': fields.Datetime.now()})
            # ~ rec.input_move_lines._action_done()
            # ~ rec.output_move_lines._action_done()
            rec.state = 'done'
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
    lot_id = fields.Many2one('stock.production.lot', string="Lot")
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
        if self.input_transfer_id:
            return self.get_validation_message()

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.name = line.product_id.name
                line.product_uom = line.product_id.uom_id and line.product_id.uom_id.id or False
                line.uom_id = line.product_id.uom_id and line.product_id.uom_id.id or False
                if line.input_transfer_id:
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
    

