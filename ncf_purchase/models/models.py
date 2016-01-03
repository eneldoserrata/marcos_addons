# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions

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
        piking_ids = self.get_user_picking()
        if piking_ids:
            return piking_ids[0]

        return 0

    picking_type_id = fields.Many2one('stock.picking.type', 'Hello', states=READONLY_STATES, required=True, default=_default_picking_type,\
    help="This will determine picking type of incoming shipment")

    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', oldname='fiscal_position')

    def get_user_picking(self):
        user_shop_domain = self.env["shop.ncf.config"].get_user_shop_domain()
        user_shops = self.env["shop.ncf.config"].search(user_shop_domain)
        warehouse_ids = [r.id for r in user_shops.warehouse_ids]
        picking_type_ids = [r.id for r in self.env["stock.picking.type"].search([('warehouse_id','in',warehouse_ids),
                                                                                 ('code','=','incoming')])]
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
        if self.fiscal_position_id:
            self.partner_id.property_account_position_supplier_id = self.fiscal_position_id.id;

    @api.onchange("date_planed")
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