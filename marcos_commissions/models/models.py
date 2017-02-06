# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
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

from openerp import models, fields, api

from datetime import datetime, timedelta


class ResPartner(models.Model):
    _inherit = "res.partner"

    employee_id = fields.Many2one("hr.employee", string="Vendedor asignado")


class CommisionsConfig(models.Model):
    _name = 'commissions.config'

    name = fields.Char("Nombre")
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

    @api.multi
    @api.depends("date_start","date_end","employee_id")
    def _get_name(self):
        self.name = "{} del {} al {}".format(self.employee_id.name, self.date_start, self.date_end)

    name = fields.Char("Nombre", compute="_get_name")
    date_start = fields.Date("Fechas inicial", required=True)
    date_end = fields.Date("Fechas final", required=True)
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    state = fields.Selection([("draft", "Borrador"), ("paid", "Pagada")], default="draft")
    commission_detail_ids = fields.One2many("commission.report.detail", "commission_report_id")
    company_currency_id = fields.Many2one("res.currency", default=74)

    def get_invoice_commissions(self, invoice_ids, commissions_config, payment_id):
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
                                      "sale_payment_amount": res["paid"],
                                      "payment_id": payment_id}))
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

                        payment_ids = self.env["account.payment"].search([('partner_id','=',partner_id.id),
                                                                          ('partner_type','=','customer'),
                                                                          ('payment_date','>=',self.date_start),
                                                                          ('payment_date', '<=', self.date_end),
                                                                          ('state','in',['posted','sent','reconciled'])])
                        for payment_id in payment_ids:
                            invoice_ids = payment_id.invoice_ids.filtered(lambda r: r.state == "paid")

                            invoice_commissions = self.get_invoice_commissions(invoice_ids, commissions_config, payment_id.id)
                            if invoice_commissions:
                                self.write({"commission_detail_ids": invoice_commissions})

    @api.multi
    def confirm_report(self):
        self.state = "paid"

    @api.multi
    def get_report_data(self):
        report_detail = {}
        for line in self.commission_detail_ids:
            if not line.partner_id.name in report_detail.keys():
                report_detail.update({line.partner_id.name: []})
            report_detail[line.partner_id.name].append({"payemnt_date":line.payemnt_date,
                                                        "payment_id": line.payment_id.name,
                                                        "invoice_date": line.invoice_date,
                                                        "invoice_id": line.invoice_id.number,
                                                        "amount_untaxed": line.amount_untaxed,
                                                        "amount": line.amount,
                                                        })
        lista = []
        for item in report_detail.items():
            lista.append(item)

        return lista


class CommissionReportDetail(models.Model):
    _name = "commission.report.detail"

    @api.multi
    def _get_commission_total(self):
        for rec in self:
            rec.amount = rec.sale_commission_amount + rec.sale_payment_amount

    commission_report_id = fields.Many2one("commission.report")
    payment_id = fields.Many2one("account.payment", string="Pago")
    payemnt_date = fields.Date(string="Fecha del Pago", related="payment_id.payment_date")
    invoice_id = fields.Many2one("account.invoice", string="Factura / Referencia")
    invoice_date = fields.Date(related="invoice_id.date_invoice", string="Fecha de la factura")
    partner_id = fields.Many2one("res.partner", related="invoice_id.partner_id", string="Cliente")
    company_currency_id = fields.Many2one("res.currency", default=74)
    amount_untaxed = fields.Monetary(related="invoice_id.amount_untaxed_signed", string="Monto sin impuesto",
                                     currency_field="company_currency_id")
    sale_commission_amount = fields.Monetary(u"Comisión por venta", currency_field="company_currency_id")
    sale_payment_amount = fields.Monetary(u"Comisión por cobro", currency_field="company_currency_id")
    amount = fields.Monetary("Monto", compute=_get_commission_total, currency_field="company_currency_id")
