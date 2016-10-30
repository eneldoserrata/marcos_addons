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


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    @api.model
    def default_get(self, fields_list):
        res = super(StockReturnPicking, self).default_get(fields_list)

        active_id = self._context.get("active_id", False)
        if active_id:
            picking = self.env["stock.picking"].browse(active_id)

            if picking.refund_action == "invoice_refund":
                raise exceptions.ValidationError(u"""Este conduce no puede ser devuelto porque fue emitida una nota de crédito."
                                           esto ocurre cuando el conduce que origino este reverso pertenece a una compra o
                                           venta y al recibir o al entregar la mercancia esta solicito la emision de una
                                           nota de crédito para el rembolso del pago.""")

            # TODO test this constraing prevent refund
            if not self._context.get("refund_action", False):
                if res.get("product_return_moves"):
                    if sum([l[2]["quantity"] for l in res["product_return_moves"]]) == 0:
                        raise exceptions.ValidationError(u"Este conduce ya fue totalmente devuelto")

            if picking.purchase_id:
                refund_action = "in_refund"
            elif picking.sale_id:
                refund_action = "out_refund"
            else:
                refund_action = "internal"

            invoice_id = False
            if refund_action == "in_refund":
                invoice_lines = self.env["account.invoice.line"].search([('purchase_id', '=', picking.purchase_id.id),('invoice_id.type','=','in_invoice')])
                if invoice_lines:
                    invoice_id = invoice_lines.mapped("invoice_id")
            # elif refund_action == "out_refund":
            #     invoice_lines = self.env["sale.order.line"].search([('order_id', '=', picking.sale_id.id)])
            #     if invoice_lines:
            #         try:
            #             invoice_id = invoice_lines.invoice_lines.mapped("invoice_id")
            #         except:
            #             invoice_id = False

            res.update({"invoice_id": False, "refund_action": "change", "picking_id": picking.id})

            if refund_action == "out_refund":
                res.update({"invoice_id": False, "refund_action": "none", "picking_id": picking.id, "out_refund": True})

            if invoice_id:
                res.update({"invoice_id": invoice_id.id, "refund_action": "invoice_refund"})

            return res

    refund_action = fields.Selection(
        [('invoice_refund', u"Solicitar nota de crédito"),
         ("change", "Para realizar cambio"),
         ("none", "Otros"),
         ],
        string=u"Acción", readonly=False, required=True)
    out_refund = fields.Boolean("El origen es una venta", default=False)
    invoice_id = fields.Many2one("account.invoice", string="Comprobante que afecta", readonly=True)
    due_date = fields.Datetime(string="Fecha prevista")
    picking_id = fields.Many2one("stock.picking")
    note = fields.Char("Motivo")


    @api.multi
    def create_returns(self):
        res = super(StockReturnPicking, self).create_returns()
        if self.refund_action == "invoice_refund" and not self.invoice_id:
                raise exceptions.ValidationError(u"Para solicitar una nota de crédito por la devolucion de este conduce,"
                                                 u"primero debe de estar generada la factura.")
        new_picking = self.env["stock.picking"].browse(res.get("res_id"))
        new_picking.refund_action = self.refund_action
        if self.due_date:
            new_picking.min_date = self.due_date
        if self.note:
            message = "<b><strong>Motivo para el reverso: </strong>{}</b>".format(self.note)
            new_picking.message_post(message)

        return res
