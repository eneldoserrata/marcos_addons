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


from odoo import models, fields, api, exceptions
import base64
import odoo.addons.decimal_precision as dp


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
    print_source = fields.Selection([('server', 'Desde el servidor'), ('browser', 'Desde el navegador de internet')],
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
        filename = "LV{}{}{}.000".format(date[0][2:4], date[1], date[2])

        book = self.env["ipf.daily.book"].search([('serial', '=', serial), ('date', '=', bookday)])
        if book:
            book.unlink()

        values = {"printer_id": printer_id, "date": bookday, "book": base64.b64encode(new_book), "serial": serial,
                  "filename": filename}

        new_book = self.env["ipf.daily.book"].create(values);

        self.set_book_totals(new_book)

        return True

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
        if self._context.get("active_model", False) == "pos.order" and nif:
            self._cr.execute("update pos_order set fiscal_nif = '{}' where id = {}".format(nif, id))
        elif nif:
            self._cr.execute("update account_invoice set fiscal_nif = '{}' where id = {}".format(nif, id))

        return True

    @api.model
    def ipf_print(self):
        active_id = self._context.get("active_id", False)
        if active_id and self._context.get("active_model", False) == "account.invoice":
            invoice_id = self.env["account.invoice"].browse(active_id)
            return invoice_id.get_ipf_dict()
        elif active_id and self._context.get("active_model", False) == "pos.order":
            invoice_id = self.env["pos.order"].browse(active_id).invoice_id
            if invoice_id:
                return invoice_id.get_ipf_dict()


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
    fiscal_total_tax = fields.Float("Fiscal Itbis total", digits=dp.get_precision('Account'))
    ncfinal_total = fields.Float("NC final total", digits=dp.get_precision('Account'))
    ncfinal_total_tax = fields.Float("NC final Itbis total", digits=dp.get_precision('Account'))
    ncfiscal_total = fields.Float("NC fiscal total", digits=dp.get_precision('Account'))
    ncfiscal_total_tax = fields.Float("NC fiscal Itbis total", digits=dp.get_precision('Account'))
