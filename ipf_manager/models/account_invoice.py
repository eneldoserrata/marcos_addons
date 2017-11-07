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

from odoo import models, fields, exceptions

import re


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    fiscal_nif = fields.Char("NIF", default="false", copy=False)

    def ncf_fiscal_position_exception(self, partner_name):
        raise exceptions.UserError(
            u"El tipo de comprobante no corresponde a la posicion fical del cliente '%s'!" % (partner_name))

    def get_ipf_dict(self):
        if self.amount_total == 0:
            raise exceptions.UserError("No se puede imprimir en la impresora fiscal una factura valor 0.")

        ipf_printer = self.env["ipf.printer.config"].search([('subsidiary', '=', self.shop_id.id),('user_ids','=',self.env.user.id)])

        if not ipf_printer:
            raise exceptions.UserError("Su usuario no tiene impresora fiscal asignada")

        invoice_dict = {}
        print_copy = ipf_printer.print_copy
        subsidiary = ipf_printer.subsidiary

        invoice_dict["type"] = "nofiscal"
        if self.state in ['open', 'paid'] and self.fiscal_nif == "false":
            invoice_dict["ncf"] = self.number

            ncf_type = self.sale_fiscal_type

            if self.type == "out_invoice":
                if ncf_type == "gov":
                    invoice_dict["type"] = "fiscal"
                else:
                    invoice_dict["type"] = ncf_type
                    if not invoice_dict["type"]:
                        invoice_dict["type"] = "final"
            elif self.type == "out_refund":
                ncf_type = self.sale_fiscal_type or "final"
                invoice_dict["reference_ncf"] = self.origin
                if ncf_type == "final":
                    invoice_dict["type"] = "final_note"
                elif ncf_type in ["fiscal", "gov"]:
                    invoice_dict["type"] = "fiscal_note"
                elif ncf_type == "special":
                    invoice_dict["type"] = "special_note"

            if self.type in ("out_invoice"):
                if ncf_type == "fiscal":
                    if not self.number[9:-8] == "01":
                        return self.ncf_fiscal_position_exception(self.partner_id.name)
                elif ncf_type == "special":
                    if not self.number[9:-8] == "14":
                        return self.ncf_fiscal_position_exception(self.partner_id.name)
                elif ncf_type == "gov":
                    if not self.number[9:-8] == "15":
                        return self.ncf_fiscal_position_exception(self.partner_id.name)
                elif invoice_dict["type"] in ["final_note", "fiscal_note", "special_note"]:
                    if not self.number[9:-8] == "04":
                        return self.ncf_fiscal_position_exception(self.partner_id.name)
                elif invoice_dict["type"] == "final":
                    if not self.number[9:-8] == "02":
                        return self.ncf_fiscal_position_exception(self.partner_id.name)
        else:
            invoice_dict["type"] = "nofiscal"

        invoice_dict["copy"] = print_copy
        invoice_dict["cashier"] = self.env.uid
        invoice_dict["subsidiary"] = subsidiary.id
        invoice_dict["client"] = self.partner_id.name
        invoice_dict["rnc"] = self.partner_id.vat

        invoice_items_list = []
        for line in self.invoice_line_ids:
            invoice_items_dict = {}
            description = re.sub(r'^\[[\s\d]+\]\s+', '', line.name).strip()
            description = re.sub(r'[^\w.]', ' ', description)

            description_splited = [description[x:x + 21].replace("\n", "") for x in range(0, len(description), 21)]

            invoice_items_dict["description"] = description_splited.pop()

            if len(description_splited) > 0:
                invoice_items_dict["extra_descriptions"] = description_splited[0:9]

            extra_description = []
            # if not variant_name == line.name:
            #     extra_description += line.name.split("\n")
            if extra_description:
                invoice_items_dict["extra_description"] = extra_description[0:9]
            invoice_items_dict["quantity"] = line.quantity

            tax_id = line.invoice_line_tax_ids

            if not len(tax_id) == 1:
                raise exceptions.UserError(
                    u"Los productos de ventas deben de tener un impuesto asignado y nunca mas de uno revise el '%s'!" % (
                    line.name))

            tax_rate = int(tax_id.amount)
            tax_include = tax_id.price_include
            tax_except = tax_id.tax_except

            if not tax_rate in [18, 13, 11, 8, 5, 0]:
                raise exceptions.UserError(
                    u"Los productos de ventas contiene un porcentaje de impuesto inválido %s" % (line.name))

            invoice_items_dict["itbis"] = tax_rate
            if tax_include or tax_except:
                invoice_items_dict["price"] = line.price_unit
            else:
                invoice_items_dict["price"] = line.price_unit + (line.price_unit * (tax_id.amount / 100))

            if line.discount > 0:
                invoice_items_dict["discount"] = line.discount

            invoice_items_list.append(invoice_items_dict)

        invoice_dict["items"] = invoice_items_list

        payment_ids_list = []

        if not len(self.payment_move_line_ids) == 0:
            for payment in self.payment_move_line_ids:
                if payment.credit:
                    payment_ids_dict = {}
                    payment_ids_dict["type"] = payment.journal_id.ipf_payment_type or "Nota de credito {}".format(
                        payment.name)
                    payment_ids_dict["amount"] = payment.credit
                    payment_ids_list.append(payment_ids_dict)
                else:
                    payment_ids_dict = {}
                    payment_ids_dict["type"] = payment.journal_id.ipf_payment_type or "other"
                    payment_ids_dict["amount"] = payment.debit
                    payment_ids_list.append(payment_ids_dict)
        else:
            payment_ids_list.append(dict(type="other", amount=self.amount_total))

        if invoice_dict["type"] == "nofiscal":
            invoice_dict.update(dict(host=ipf_printer.host, payments=payment_ids_list, invoice_id=self.id))
        else:
            invoice_dict.update(dict(host=ipf_printer.host, payments=payment_ids_list, invoice_id=self.id))
        return invoice_dict
