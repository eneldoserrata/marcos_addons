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
from openerp import models, fields, api, exceptions
from openerp.tools.translate import _



class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_id = fields.Many2one("purchase.order", string="Pedido de compra", readonly=True, copy=False)
    refund_action = fields.Selection(
        [('invoice_refund', u"Con nota de crédito solicitada"),
         ("change", "Para realizar cambio"),
         ("none", "Otros")],
        string=u"Tipo de devolución", readonly=True, required=False, copy=False)

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        if self.refund_action == "invoice_refund":
            origin_picking = self.search([('name', '=', self.origin)])

            if origin_picking.purchase_id:
                refund_action = "in_refund"
            elif origin_picking.sale_id:
                refund_action = "out_refund"

            invoice_id = False
            if refund_action == "in_refund":
                invoice_lines = self.env["account.invoice.line"].search(
                    [('purchase_id', '=', origin_picking.purchase_id.id)])
                if invoice_lines:
                    invoice_id = invoice_lines.mapped("invoice_id")
            elif refund_action == "out_refund":
                invoice_lines = self.env["sale.order.line"].search([('order_id', '=', origin_picking.sale_id.id)])
                if invoice_lines:
                    invoice_id = invoice_lines.invoice_lines.mapped("invoice_id")

            refund_invoice = invoice_id.refund()
            refund_invoice.ncf_required = invoice_id.ncf_required
            refund_invoice.invoice_line_ids.unlink()

            for line in self.move_lines:
                purchase_line_id = line.origin_returned_move_id.purchase_line_id.id
                origin_invoice_line = self.env["account.invoice.line"].search(
                    [("purchase_line_id", "=", purchase_line_id)])
                new_invoice_line = origin_invoice_line.copy(
                    {"invoice_id": refund_invoice.id, "quantity": line.product_qty})
                new_invoice_line._compute_price()


            refund_invoice.compute_taxes()
            refund_invoice._compute_amount()
        elif self.refund_action == "change":

            context = dict(self._context)
            context.update({"refund_action": "none", "active_id": self.id})

            refund_wizard = self.env["stock.return.picking"].with_context(context).create(
                {"refund_action": "none", "min_date": self.min_date})
            refund_wizard._create_returns()

        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def product_price_update_after_done(self):
        super(StockMove, self).product_price_update_after_done()
        for move in self:
            if move.product_id.cost_method == 'real' and move.location_dest_id.usage == 'internal' and move.product_id.standard_price == 0:
                self._store_average_cost_price(move)
