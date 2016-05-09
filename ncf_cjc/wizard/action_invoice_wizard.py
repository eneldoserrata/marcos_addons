# -*- coding: utf-8 -*-

from openerp import fields, models, api, exceptions


class CjcActionInvoice(models.TransientModel):
    _name = "cjc.invoice.wizard"

    @api.model
    def _journal_domain(self):
        if self.env.user.employee_ids.cjc_journa_ids:
            return [('id','in',[j.id for j in self.env.user.employee_ids.cjc_journa_ids if j.type == 'cash'])]
        else:
            return [('type','=','purchase'),('petty_cash','=',True)]

    @api.model
    def _default_journal(self):
        if self.env.user.employee_ids.cjc_journa_ids:
            return self.env.user.employee_ids.cjc_journa_ids[0].id
        else:
            cjc_journal = self.env["account.journal"].search([('type','=','purchase'),('petty_cash','=',True)])
            if cjc_journal:
                return cjc_journal[0].id
            else:
                raise exceptions.ValidationError("No sean cofigurado diarios de compras para ser usados en caja chica")


    @api.model
    def _compute_amount(self):
        self.amount_total = 0;
        for line in self.line_ids:
            self.amount_total += line.amount

    statement_id = fields.Many2one('account.bank.statement')
    statement_line_id = fields.Many2one("account.bank.statement.line")
    journal_id = fields.Many2one("account.journal", string="Diario de compra", domain=_journal_domain, required=True,
                                 default=_default_journal)
    purchase_type = fields.Selection([("normal",u"Proveedor normal"),
                                      ("minor", u"Gasto menor"),
                                      ("informal", u"Proveedor informal"),
                                      ("exterior", u"Pagos al exterior"),
                                      ("import", u"Importaciones"),
                                      ], related="journal_id.purchase_type",
                                     string=u"Tipo de compra", default="normal")
    date_invoice = fields.Date(string="Fecha", default=fields.Date.today())
    partner_id = fields.Many2one("res.partner", string="Proveedor", domain=[('supplier', '=', True)])
    fiscal_posistion_id = fields.Many2one("account.fiscal.position", string="Tipo de gasto",
                                          domain=[('supplier', '=', True)], required=True, default=[('supplier_fiscal_type','=','02')])
    ncf = fields.Char("NCF", size=19)
    name = fields.Char("Nota del gasto", required=True)
    line_ids = fields.One2many("cjc.invoice.detail.wizard", "master_id")
    amount_total = fields.Float(string="Total", compute=_compute_amount)


class CjcActionInvoiceDetail(models.TransientModel):
    _name = "cjc.invoice.detail.wizard"

    @api.model
    def _compute_amount(self):
        self.amount = self.quantity*self.price

    master_id = fields.Many2one("cjc.invoice.wizard")
    product_id = fields.Many2one("product.product", string="Producto")
    name = fields.Char(u"Descripción", required=True)
    quantity = fields.Float("Cantidad", required=True, deafult=1)
    price = fields.Float("Precio", required=True)
    amount = fields.Float(compute=_compute_amount, string="Total")

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.name = self.product_id.name

    @api.onchange("quantity", "price")
    def onchange_quantity_price(self):
        self._compute_amount()
        self.master_id.amount_total = 100
