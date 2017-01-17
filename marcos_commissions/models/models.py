# -*- coding: utf-8 -*-

from openerp import models, fields, api

from datetime import datetime, timedelta


class ResPartner(models.Model):
    _inherit = "res.partner"

    employee_id = fields.Many2one("hr.employee", string="Vendedor asignado")


class CommisionsConfig(models.Model):
    _name = 'commissions.config'

    name = fields.Char("Nombre")
    max_days = fields.Integer(u"Antigüedad de la factura en días permitidos para considerar la comisión")
    employee_ids = fields.Many2many("hr.employee", string="Vendedores")
    commission_category_ids = fields.One2many("commission.category", "commission_config_id")
    commission_product_ids = fields.One2many("commision.product", "commission_config_id")


class CommissionCatgory(models.Model):
    _name = 'commission.category'

    commission_config_id = fields.Many2one("commissions.config")
    category_id = fields.Many2one("product.category", string=u"Categoría", required=True)
    sale_comission_percent = fields.Float(u"Comisión por venta")
    payment_comission_percent = fields.Float(u"Comisión al cobro")


class CommissionProduct(models.Model):
    _name = 'commision.product'

    commission_config_id = fields.Many2one("commissions.config")
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    sale_comission_percent = fields.Float(u"Comisión por venta")
    payment_comission_percent = fields.Float(u"Comisión al cobro")


class CommissionReport(models.Model):
    _name = "commission.report"

    date = fields.Datetime("Fechas", required=True, default=fields.Datetime.now())
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    state = fields.Selection([("draft", "Borrador"), ("paid", "Pagada")], default="draft")
    commission_detail_ids = fields.One2many("commission.report.detail", "commission_report_id")
    company_currency_id = fields.Many2one("res.currency", default=74)

    def get_invoice_commissions(self, invoice_ids, commissions_config):
        commission_category = dict(
            [(pc.category_id.id, (pc.sale_comission_percent, pc.payment_comission_percent)) for pc in
             commissions_config.commission_category_ids])
        commission_product = dict(
            [(pc.product_id.id, (pc.sale_comission_percent, pc.payment_comission_percent)) for pc in
             commissions_config.commission_product_ids])
        result = []

        for invoice_id in invoice_ids:
            res = {"sale": 0, "paid": 0}

            sale_commission_paid = self.env["commission.report.detail"].search([('invoice_id', '=', invoice_id.id),
                                                                                ('sale_commission_amount', '!=', 0)])

            paid_commission_paid = self.env["commission.report.detail"].search([('invoice_id', '=', invoice_id.id),
                                                                                ('sale_payment_amount', '!=', 0)])

            for invoice_line in invoice_id.invoice_line_ids:

                if invoice_line.product_id.id in commission_product.keys():
                    if not sale_commission_paid:
                        sale_comission = commission_product[invoice_line.product_id.id][0]
                        if sale_comission:
                            res["sale"] += ((
                                            invoice_line.price_subtotal_signed * sale_comission) / 100)
                    if not paid_commission_paid:
                        paid_comission = commission_product[invoice_line.product_id.id][1]
                        if paid_comission:
                            res["paid"] += ((
                                            invoice_line.price_subtotal_signed * paid_comission) / 100)

                elif invoice_line.product_id.categ_id.id in commission_category.keys():
                    if not sale_commission_paid:
                        paid_comission = commission_category[invoice_line.product_id.categ_id.id][0]
                        if paid_comission:
                            res["sale"] += ((invoice_line.price_subtotal_signed * paid_comission) / 100)

                    if not paid_commission_paid:
                        paid_comission = commission_category[invoice_line.product_id.categ_id.id][1]
                        if paid_comission:
                            res["paid"] += ((invoice_line.price_subtotal_signed * paid_comission) / 100)

            if sum(res.values()) != 0:
                result.append((0, 0, {"invoice_id": invoice_id.id,
                                      "sale_commission_amount": res["sale"],
                                      "sale_payment_amount": res["paid"]}))
        return result

    @api.multi
    def generate_report(self):
        for rec in self:
            self.commission_detail_ids.unlink()

            commissions_config = self.env["commissions.config"].search([('employee_ids', 'in', [rec.employee_id.id])])
            if commissions_config:
                partner_ids = self.env["res.partner"].search([('employee_id', '=', rec.employee_id.id)])
                if partner_ids:
                    for partner_id in partner_ids:

                        if commissions_config.max_days > 0:
                            date_invoice = datetime.today() - timedelta(days=commissions_config.max_days)
                            date_invoice = date_invoice.strftime('%Y-%m-%d')
                            domain = [('partner_id', '=', partner_id.id),
                                      ('type', 'in', ['out_invoice', 'out_refund']),
                                      ('date_invoice', '>', date_invoice),
                                      ('state', 'in', ['open', 'paid'])]
                        else:
                            domain = [('partner_id', '=', partner_id.id),
                                      ('type', 'in', ['out_invoice', 'out_refund']),
                                      ('state', 'in', ['open', 'paid'])]

                        invoice_ids = self.env["account.invoice"].search(domain)

                        invoice_commissions = self.get_invoice_commissions(invoice_ids, commissions_config)
                        if invoice_commissions:
                            self.write({"commission_detail_ids": invoice_commissions})

    @api.multi
    def confirm_report(self):
        self.state = "paid"


class CommissionReportDetail(models.Model):
    _name = "commission.report.detail"

    @api.multi
    def _get_commission_total(self):
        for rec in self:
            rec.amount = rec.sale_commission_amount + rec.sale_payment_amount

    commission_report_id = fields.Many2one("commission.report")
    invoice_id = fields.Many2one("account.invoice", string="Factura")
    invoice_date = fields.Date(related="invoice_id.date_invoice", string="Fecha de la factura")
    partner_id = fields.Many2one("res.partner", related="invoice_id.partner_id", string="Cliente")
    company_currency_id = fields.Many2one("res.currency", default=74)
    sale_commission_amount = fields.Monetary(u"Comisión por venta", currency_field="company_currency_id")
    sale_payment_amount = fields.Monetary(u"Comisión por cobro", currency_field="company_currency_id")
    amount = fields.Monetary("Monto", compute=_get_commission_total, currency_field="company_currency_id")
