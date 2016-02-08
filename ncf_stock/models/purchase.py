# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _create_picking(self):
        res = super(PurchaseOrder, self)._create_picking()
        self.env["stock.picking"].search([('group_id','=',self.group_id.id)]).write({"purchase_id": self.id})
        return res