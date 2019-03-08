# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib

from werkzeug import urls

from odoo import api, fields, models, _


import logging

_logger = logging.getLogger(__name__)


class StockTransfer(models.Model):
    _name = 'stock.transfer'

    name = fields.Char(string='Description',)
    stock_transfer_line = fields.One2many('stock.transfer.line','stock_transfer_id',string='Transfer Lines')
    state = fields.Selection([('draft','Draft'),('confirm','confirm'),('cancel','cancel')],'State',default="draft")
    
    @api.multi
    def confirm(self):
        for stocktransfer in self:
            stock_move_obj = self.env['stock.move']
            stock_move_line_obj = self.env['stock.move.line']
            for line in stocktransfer.stock_transfer_line:
                stock_vals = {
                'product_id':line.from_product_id and line.from_product_id.id,
                'product_uom':line.from_product_uom_id and line.from_product_uom_id.id,
                'product_uom_qty':line.product_uom_qty,
                'location_id':line.from_location_id and line.from_location_id.id,
                'location_dest_id':line.from_location_dest_id and line.from_location_dest_id.id,
                'name':line.from_product_id and line.from_product_id.name,
                }
                stock_move = stock_move_obj.create(stock_vals)
                stock_move_line_vals = {
                'product_id':line.to_product_id and line.to_product_id.id,
                'product_uom_id':line.to_product_uom_id and line.to_product_uom_id.id,
                'product_uom_qty':line.product_uom_qty,
                'location_id':line.to_location_id and line.to_location_id.id,
                'location_dest_id':line.to_location_dest_id and line.to_location_dest_id.id,
                'name':line.to_product_id and line.to_product_id.name,
                'move_id':stock_move and stock_move.id,
                }
                stock_move_line_obj.create(stock_move_line_vals)
                stock_move._action_confirm()
                stock_move._action_done()
                line.write({'move_id':stock_move.id})
            stocktransfer.write({'state':'confirm'})
        return True
            
    @api.multi
    def cancel(self):
        for stocktransfer in self:
            for line in stocktransfer.stock_transfer_line:
                line.stock_move.action_cancel()
            stocktransfer.write({'state':'cancel'})

    @api.multi
    def reset(self):
        for stocktransfer in self:
            stocktransfer.write({'state':'draft'})
        


class StockTransferLine(models.Model):
    _name = 'stock.transfer.line'
    
    from_product_id = fields.Many2one('product.product','Product One',required=True)
    to_product_id = fields.Many2one('product.product','Product Two',required=True)
    from_product_uom_id = fields.Many2one('product.uom','Product One UOM',required=True)
    to_product_uom_id = fields.Many2one('product.uom','Product Two UOM',required=True)
    product_uom_qty = fields.Float('Product Qty')
    from_location_id = fields.Many2one('stock.location','Product One Source',required=True)
    from_location_dest_id = fields.Many2one('stock.location','Product One Destination',required=True)
    to_location_id = fields.Many2one('stock.location','Product Two Source',required=True)
    to_location_dest_id = fields.Many2one('stock.location','Product Two Destination',required=True)
    move_id = fields.Many2one('stock.move','Moves')
    stock_transfer_id = fields.Many2one('stock.transfer','Stock Transfer')

