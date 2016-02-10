# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


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
                invoice_lines = self.env["account.invoice.line"].search([('purchase_id', '=', picking.purchase_id.id)])
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
