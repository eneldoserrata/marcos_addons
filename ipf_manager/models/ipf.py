# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013-2015 Marcos Organizador de Negocios SRL http://marcos.do
#    Write by Eneldo Serrata (eneldo@marcos.do)
#
##############################################################################


from openerp import models, fields, api, exceptions
import re
import base64
import openerp.addons.decimal_precision as dp


class ipf_printer_config(models.Model):
    _name = 'ipf.printer.config'

    def _user_ids_filter(self):
        domain = []
        printers = self.search([])
        for printer in printers:
            for user in printer.user_ids:
                if user.id not in [domain]:
                    domain.append(user.id)
        if not domain:
            return domain
        return [("user_ids", "not in", domain)]

    name = fields.Char("Descripcion", required=True)
    host = fields.Char("Host", required=True)
    print_source = fields.Selection([('server','Desde el servidor'),('browser','Desde el navegador de internet')],
                                    string="Fuente de impresion", default="browser", required=True,
                                    help="""
                                    Desde el navegador de internet: Los comandos seran enviados a la impresora desde
                                    su navegador de internet google Chrome con la extencion de marcos instalada y activada,
                                     (Solo funciona con google Chrome).
                                     <br/>
                                     Desde el servidor: Los comandos seran enviados al servidor de odoo y este enviara
                                     los comandos de impresion a la impresora fiscal, debe de tener en cuanta la configuracion
                                     de router en caso de tener Odoo hosteado en la nube.
                                    """)
    user_ids = fields.Many2many('res.users', string="Usuarios", required=True, domain=_user_ids_filter)
    print_copy = fields.Boolean("Imprimir con copia", default=False)
    subsidiary = fields.Many2one("shop.ncf.config", string="Sucursal", required=True)
    daily_book_ids = fields.One2many("ipf.daily.book", "printer_id", string="Libros diarios")
    state = fields.Selection([("deactivate", "Desactivada"), ("active", "Activa")], default="deactivate")
    serial = fields.Char("Serial de la impresora", readonly=True)

    def set_book_totals(self, book):
        book_header_sun = [0, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
        daily_book_row = base64.b64decode(book.book).split("\n")

        for row in daily_book_row:
            field_list = row.split("||")
            if field_list[0] == "1":
                book_header_sun[0] += int(field_list[3]) if field_list[3] else 0
                book_header_sun[1] += float(field_list[4]) if field_list[4] else 0.00
                book_header_sun[2] += float(field_list[5]) if field_list[5] else 0.00
                book_header_sun[3] += float(field_list[11]) if field_list[11] else 0.00
                book_header_sun[4] += float(field_list[12]) if field_list[12] else 0.00
                book_header_sun[5] += float(field_list[14]) if field_list[14] else 0.00
                book_header_sun[6] += float(field_list[15]) if field_list[15] else 0.00
                book_header_sun[7] += float(field_list[17]) if field_list[17] else 0.00
                book_header_sun[8] += float(field_list[18]) if field_list[18] else 0.00
                book_header_sun[9] += float(field_list[20]) if field_list[20] else 0.00
                book_header_sun[10] += float(field_list[21]) if field_list[21] else 0.00

        values = {
            "doc_qty": book_header_sun[0],
            "total": book_header_sun[1],
            "total_tax": book_header_sun[2],
            "final_total": book_header_sun[3],
            "final_total_tax": book_header_sun[4],
            "fiscal_total": book_header_sun[5],
            "fiscal_total_tax": book_header_sun[6],
            "ncfinal_total": book_header_sun[7],
            "ncfinal_total_tax": book_header_sun[8],
            "ncfiscal_total": book_header_sun[9],
            "ncfiscal_total_tax": book_header_sun[10],
        }

        return book.write(values)

    @api.model
    def save_book(self, new_book, serial, bookday):
        printer_id = self.get_ipf_host(get_id=True)
        date = bookday.split("-")
        filename = "LV{}{}{}.000".format(date[0][2:4],date[1],date[2])

        book = self.env["ipf.daily.book"].search([('serial', '=', serial), ('date', '=', bookday)])
        if book:
            book.unlink()

        values = {"printer_id": printer_id, "date": bookday, "book": base64.b64encode(new_book), "serial": serial, "filename": filename}

        new_book = self.env["ipf.daily.book"].create(values);

        self.set_book_totals(new_book)

        return True

    def ncf_fiscal_position_exception(self, partner_name):
        raise exceptions.Warning(u'Tipo de comprobante fiscal inválido!',
                u"El tipo de comprobante no corresponde a la posicion fical del cliente '%s'!" % (partner_name))

    @api.model
    def get_user_printer(self):
        return self.search([("user_ids", "=", self.env.uid)])

    @api.model
    def get_ipf_host(self, get_id=False):
        printer = False

        if self._context.get("active_model", False) == "ipf.printer.config":
            printer = self.browse(self._context["active_id"])
        else:
            printer = self.get_user_printer()

        if printer:
            if get_id:
                return printer.id
            else:
                return {"host": printer.host}
        else:
            raise exceptions.Warning("Las impresoras fiscales no estan configuradas!")

    @api.model
    def print_done(self, values):
        id = values[0]
        nif = values[1]
        if not nif == None:
            self.pool.get("account.invoice").write(self.env.cr, self.env.uid, id, {"nif": nif})
        return True

    @api.model
    def ipf_print(self):
        invoice = False
        if self.env.context.get("active_model", False) == "account.invoice":
            invoice = self.env["account.invoice"].browse(self.env.context.get("active_id"))
            if self.env.context.get("ipf_host", False):
                printer_id = self.env.context.get("ipf_host", False)
                printer = self.browse(printer_id[0])
            else:
                printer = self.get_user_printer()
        elif self.env.context.get("active_model", False) == "pos.order" or self.env.context.get("active_model", False) == "pos.payment":
            invoice = self.env["pos.order"].browse(self.env.context.get("active_id")).invoice_id
            printer = self.get_user_printer()

        if invoice.amount_total == 0:
            raise exceptions.Warning("No se puede imprimir en la impresora fiscal una factura valor 0.")

        invoice_dict = {}

        print_copy = printer.print_copy
        subsidiary = printer.subsidiary

        ncf_type = False

        invoice_dict["type"] = "nofiscal"
        if invoice.state in ['open', 'paid'] and invoice.nif == "false":
            invoice_dict["ncf"] = invoice.number
            ncf_type = invoice.fiscal_position.fiscal_type

            if invoice.type == "out_invoice":
                if ncf_type == "gov":
                    invoice_dict["type"] = "fiscal"
                else:
                    invoice_dict["type"] = ncf_type
                    if not invoice_dict["type"]:
                        invoice_dict["type"] = "final"

            elif invoice.type == "out_refund":
                ncf_type = invoice.fiscal_position.fiscal_type or "final"
                invoice_dict["reference_ncf"] = invoice.parent_id.number
                if ncf_type == "final":
                    invoice_dict["type"] = "final_note"
                elif ncf_type in ["fiscal", "gov"]:
                    invoice_dict["type"] = "fiscal_note"
                elif ncf_type == "special":
                    invoice_dict["type"] = "special_note"

            if invoice.type == "out_invoice":
                if ncf_type == "fiscal":
                    if not invoice.number[9:-8] == "01":
                        return self.ncf_fiscal_position_exception(invoice.partner_id.name)
                elif ncf_type == "special":
                    if not invoice.number[9:-8] == "14":
                        return self.ncf_fiscal_position_exception(invoice.partner_id.name)
                elif ncf_type == "gov":
                    if not invoice.number[9:-8] == "15":
                        return self.ncf_fiscal_position_exception(invoice.partner_id.name)
                elif invoice_dict["type"] in ["final_note", "fiscal_note", "special_note"]:
                    if not invoice.number[9:-8] == "04":
                        return self.ncf_fiscal_position_exception(invoice.partner_id.name)
                elif invoice_dict["type"] == "final":
                    if not invoice.number[9:-8] == "02":
                        return self.ncf_fiscal_position_exception(invoice.partner_id.name)
        else:
            invoice_dict["type"] = "nofiscal"

        invoice_dict["copy"] = print_copy
        invoice_dict["cashier"] = self.env.uid
        invoice_dict["subsidiary"] = subsidiary.id
        invoice_dict["client"] = invoice.partner_id.name
        invoice_dict["rnc"] = invoice.partner_id.ref

        invoice_items_list = []
        for line in invoice.invoice_line:
            invoice_items_dict = {}
            # variant_name = self.pool.get("product.product").name_get(self.env.cr, self.env.uid, [line.product_id.id],
            #                                                          context=self.env.context)[0][1]
            # description = re.sub(r'^\[[\s\d]+\]\s+', '', variant_name).strip()
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

            tax_id = line.invoice_line_tax_id

            if not len(tax_id) == 1:
                raise exceptions.Warning(u'Error en el impuestos de productos',
                u"Los productos de ventas deben de tener un impuesto asignado y nunca mas de uno revise el '%s'!" % (line.name))

            tax_rate = int(tax_id.amount*100)
            tax_include = tax_id.price_include
            tax_except = tax_id.exempt

            if not tax_rate in [18, 13, 11, 8, 5, 0]:
                raise exceptions.Warning(u'Impuesto inválido',
                u"Los productos de ventas contiene un porcentaje de impuesto inválido %s" % (line.name))

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

        if not len(invoice.payment_ids) == 0:
            for payment in invoice.payment_ids:
                if payment.credit:
                    payment_ids_dict = {}
                    payment_ids_dict["type"] = payment.journal_id.ipf_payment_type or "other"
                    payment_ids_dict["amount"] = payment.credit
                    payment_ids_list.append(payment_ids_dict)
                else:
                    payment_ids_dict = {}
                    payment_ids_dict["type"] = payment.journal_id.ipf_payment_type or "other"
                    payment_ids_dict["amount"] = payment.debit
                    payment_ids_list.append(payment_ids_dict)
        else:
            payment_ids_list.append(dict(type="other", amount=invoice.amount_total))

        if invoice_dict["type"] == "nofiscal":
            invoice_dict.update(dict(host=printer.host, payments=payment_ids_list, invoice_id=invoice.id))
        else:
            invoice_dict.update(dict(host=printer.host, payments=payment_ids_list, invoice_id=invoice.id))
        # from pprint import pprint as pp
        # pp(invoice_dict)
        return invoice_dict


class ipf_daily_book(models.Model):
    _name = "ipf.daily.book"
    _order = "date"

    printer_id = fields.Many2one("ipf.printer.config", string="Printer", readonly=True)
    subsidiary = fields.Many2one("", string="Sucursal", related="printer_id.subsidiary")
    date = fields.Date("Fecha", readonly=True)
    serial = fields.Char("Serial", readonly=True)
    book = fields.Binary("Libro diario", readonly=True)
    filename = fields.Char("file name", readonly=True)

    doc_qty = fields.Integer("Transacciones", digits=dp.get_precision('Account'))
    total = fields.Float("Total", digits=dp.get_precision('Account'))
    total_tax = fields.Float("Total Itbis", digits=dp.get_precision('Account'))
    final_total = fields.Float("Final total", digits=dp.get_precision('Account'))
    final_total_tax = fields.Float("Final Itbis total", digits=dp.get_precision('Account'))
    fiscal_total = fields.Float("Fiscal total", digits=dp.get_precision('Account'))
    fiscal_total_tax= fields.Float("Fiscal Itbis total", digits=dp.get_precision('Account'))
    ncfinal_total = fields.Float("NC final total", digits=dp.get_precision('Account'))
    ncfinal_total_tax = fields.Float("NC final Itbis total", digits=dp.get_precision('Account'))
    ncfiscal_total = fields.Float("NC fiscal total", digits=dp.get_precision('Account'))
    ncfiscal_total_tax = fields.Float("NC fiscal Itbis total", digits=dp.get_precision('Account'  ))