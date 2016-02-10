# -*- coding: utf-8 -*-

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
