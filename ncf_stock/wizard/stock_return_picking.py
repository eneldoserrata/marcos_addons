# -*- coding: utf-8 -*-

from openerp import models, fields


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _default_invoice_action(self):
        pickin_id = self.env["stock.picking"].browse(self._context.get("active_id",0))

    invoice_action = fields.Selection(
            [("nc", u'Genera Factura'), ('inv', u"Genera Nota de Crédito"), ("int", "Conduce interno")],
            string=u"Acción", readonly=True, default=_default_invoice_action)


