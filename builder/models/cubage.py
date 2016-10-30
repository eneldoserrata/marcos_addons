# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class Cubage(models.Model):
    _name = "cubage"

    @api.multi
    def amount_totals(self):
        for rec in self:
            rec.subtotal = sum([line.sub_total for line in rec.cubage_lines])
            rec.retention_total = sum([line.retention_amount for line in rec.cubage_lines])
            rec.total = sum([line.amount_total for line in rec.cubage_lines])

    name = fields.Char(u"Cubicación")
    state = fields.Selection([('draft','Borrador'),('validate','Aprobado'),('paid','Pagado')], default="draft")
    employee_id = fields.Many2one("hr.employee", string="Contratista")
    date = fields.Date("Fecha")
    start_date = fields.Date("Fecha inicial")
    end_date = fields.Date("Fecha final")
    note = fields.Text("Nota")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    retention = fields.Float(u"Retención", default=0)
    subtotal = fields.Float("Subtotal", compute=amount_totals)
    retention_total = fields.Float("Retenido", compute=amount_totals)
    total = fields.Float("Total", compute=amount_totals)
    cubage_lines = fields.One2many("cubage.line", "cubage_id")


class CubageDetail(models.Model):
    _name = "cubage.line"

    @api.multi
    def _compute_totals(self):
        for rec in self:
            rec.sub_total = self.qty * rec.price_unit
            if rec.have_retention:
                rec.retetion_amount = rec.sub_total * rec.cubage_id.retention
            rec.amount_total = rec.sub_total - rec.retention_amount

    cubage_id = fields.Many2one("cubage")
    product_id = fields.Many2one("product.product")
    uom = fields.Many2one("product.uom", "Ud")
    categ_id = fields.Many2one("product.category", related="product_id.categ_id")
    qty = fields.Float("Cantidad")
    price_unit = fields.Float("Precio")
    sub_total = fields.Float("Subtotal", compute=_compute_totals)
    have_retention = fields.Boolean("Retiene")
    retention_amount = fields.Float(u"Retención", compute=_compute_totals)
    amount_total = fields.Float("Monto", compute=_compute_totals)

    @api.onchange
    def onchange_product_id(self):
        self.price_unit = self.product_id.standard_price
