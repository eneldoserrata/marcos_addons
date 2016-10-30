# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################
from odoo import models, fields, api, exceptions

from lxml import etree

READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _default_picking_type(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        wh_ids = shop_user_config["warehouse_ids"]
        picking_ids = [r.id for r in self.env["stock.picking.type"].search([('warehouse_id','in',wh_ids),('code','=','incoming')])]
        return picking_ids[0]

    picking_type_id = fields.Many2one('stock.picking.type', 'Hello', states=READONLY_STATES, required=True, default=_default_picking_type,\
    help="This will determine picking type of incoming shipment")

    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', oldname='fiscal_position',
                                         domain=[('supplier','=',True)])

    def get_user_picking(self):

        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        picking_type_ids = [r.id for r in self.env["stock.picking.type"].search([('warehouse_id','in',shop_user_config["warehouse_ids"]),('code','=','incoming')])]
        return picking_type_ids or False

    @api.onchange("picking_type_id")
    def onchange_picking_type_id(self):

        user_picking_ids = self.get_user_picking() or False
        if user_picking_ids:
            stock_picking_domain = "[('id', 'in', {})]".format(user_picking_ids)
            return {'domain': {"picking_type_id": stock_picking_domain}}

        return {'domain': {"picking_type_id": [('code','=','none')]}}

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):
        if self.partner_id:
            if self.fiscal_position_id:
                self.partner_id.property_account_position_supplier_id = self.fiscal_position_id.id;

    @api.onchange("date_planned")
    def onchange_date_planed(self):
        for line in self.order_line:
            line.date_planned = self.date_planned

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        super(AccountInvoice, self).purchase_order_change()
        self._onchange_partner_id()
        self.onchange_fiscal_position_id()