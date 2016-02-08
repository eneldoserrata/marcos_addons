# -*- coding: utf-8 -*-

from openerp import models, fields, exceptions

import re

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    fiscal_nif = fields.Char("NIF", default="false", copy=False)

    def get_ipf_dict(self):
        if self.amount_total == 0:
            raise exceptions.UserError("No se puede imprimir en la impresora fiscal una factura valor 0.")

        ipf_printer = self.env["ipf.printer.config"].search([('subsidiary','=',self.shop_id.id)])

        if not ipf_printer:
            raise exceptions.UserError("La sucursal para esta factura no tiene impresora fiscal asignada")


        invoice_dict = {}
        print_copy = ipf_printer.print_copy
        subsidiary = ipf_printer.subsidiary

        invoice_dict["type"] = "nofiscal"
        if self.state in ['open', 'paid'] and self.fiscal_nif == "false":
            invoice_dict["ncf"] = self.number

            ncf_type = self.fiscal_position_id.client_fiscal_type

            if self.type == "out_invoice":
                if ncf_type == "gov":
                    invoice_dict["type"] = "fiscal"
                else:
                    invoice_dict["type"] = ncf_type
                    if not invoice_dict["type"]:
                        invoice_dict["type"] = "final"
            elif self.type == "out_refund":
                ncf_type = self.fiscal_position_id.client_fiscal_type or "final"
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
        invoice_dict["rnc"] = self.partner_id.ref

        invoice_items_list = []
        for line in self.invoice_line_ids:
            invoice_items_dict = {}
            description = re.sub(r'^\[[\s\d]+\]\s+', '', line.name).strip()
            description = re.sub(r'[^\w.]', ' ', description)

            description_splited = [description[x:x+21].replace("\n","") for x in range(0,len(description),21)]

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
                raise exceptions.UserError(u"Los productos de ventas deben de tener un impuesto asignado y nunca mas de uno revise el '%s'!" % (line.name))

            tax_rate = int(tax_id.amount)
            tax_include = tax_id.price_include
            tax_except = tax_id.tax_except

            if not tax_rate in [18, 13, 11, 8, 5, 0]:
                raise exceptions.UserError(u"Los productos de ventas contiene un porcentaje de impuesto inválido %s" % (line.name))

            invoice_items_dict["itbis"] = tax_rate
            if tax_include or tax_except:
                invoice_items_dict["price"] = line.price_unit
            else:
                invoice_items_dict["price"] = line.price_unit*(tax_id.amount+1)

            if line.discount > 0:
                invoice_items_dict["discount"] = line.discount

            invoice_items_list.append(invoice_items_dict)

        invoice_dict["items"] = invoice_items_list

        payment_ids_list = []

        if not len(self.payment_move_line_ids) == 0:
            for payment in self.payment_move_line_ids:
                if payment.credit:
                    payment_ids_dict = {}
                    payment_ids_dict["type"] = payment.journal_id.ipf_payment_type or "Nota de credito {}".format(payment.name)
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


