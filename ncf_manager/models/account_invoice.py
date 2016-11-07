# -*- coding: utf-8 -*-
###############################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL.
#  (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it,
# unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without
# copying any source code or material from the Software. You may distribute
# those modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the
# Softwar or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################
from openerp import exceptions
import requests
from tools import is_ncf, _internet_on
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models

from datetime import datetime


import logging
_logger = logging.getLogger(__name__)

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _default_user_shop(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        return shop_user_config["shop_ids"][0]

    @api.one
    def _get_total_discount(self):
        total_discount = 0.0
        for line in self.invoice_line_ids:
            total_discount += line.price_unit * ((line.discount or 0.0) /
                                                 100.0)
        self.total_discount = total_discount

    @api.one
    def _get_overdue_type(self):
        overdue = self.partner_id.issued_total - self.amount_total
        credit_available = (self.partner_id.credit_limit -
                            (self.partner_id.balance - self.amount_total))

        if self.amount_total > credit_available and overdue > 0:
            self.overdue_type = "overlimit_overdue"
        elif self.amount_total > credit_available:
            self.overdue_type = "overlimit"
        elif overdue > 0:
            self.overdue_type = "overdue"
        else:
            self.overdue_type = "none"

    overdue_type = (fields.Selection([
        ('overlimit_overdue',
         u'Cliente no tiene crédito disponible y tiene facturas vencidas'),
        ('overlimit', u'Cliente no tiene crédito disponible'),
        ('overdue', u'Cliente tiene facturas vencidas'),
        ('none', 'None'),
        ], u"Estado del crédito", compute=_get_overdue_type, copy=False)
        )

    internal_number = fields.Char(u"Número de factura")
    anulation_type = fields.Selection([

        ("01", u"Deterioro de Factura Pre-impresa"),
        ("02", u"Errores de Impresión (Factura Pre-impresa)"),
        ("03", u"Impresión Defectuosa"),
        ("04", u"Duplicidad de Facturas"),
        ("05", u"Corrección de la Información"),
        ("06", u"Cambio de Productos"),
        ("07", u"Devolución de Productos"),
        ("08", u"Omisión de Productos"),
        ("09", u"Errores en Secuencia de NCF")
        ], string=u"Tipo de anulación", copy=False
        )

    shop_id = fields.Many2one("shop.ncf.config", string="Sucursal",
                              required=False, default=_default_user_shop)

    ncf_required = fields.Boolean(copy=True)
    client_fiscal_type = fields.Selection(
                            related="fiscal_position_id.client_fiscal_type")

    expense_type = fields.Selection([
        ('01', u'01 - Gastos de Personal'),
        ('02', u'02 - Gastos por Trabajo, Suministros y Servicios'),
        ('03', u'03 - Arrendamientos'),
        ('04', u'04 - Gastos de Activos Fijos'),
        ('05', u'05 - Gastos de Representación'),
        ('06', u'06 - Otras Deducciones Admitidas'),
        ('07', u'07 - Gastos Financieros'),
        ('08', u'08 - Gastos Extraordinarios'),
        ('09', u'09 - Compras y Gastos que forman parte del Costo de Venta'),
        ('10', u'10 - Adquisiciones de Activos'),
        ('11', u'11 - Gastos de Seguro'),
        ], string=u"Tipo de gasto")

    purchase_type = fields.Selection(
        [("normal", u"Requiere NCF"),
         ("minor", u"Gasto Menor. NCF Generado por el Sistema"),
         ("informal", u"Proveedores Informales. NCF Generado por el Sistema"),
         ("exterior", u"Pagos al Exterior. NCF Generado por el Sistema"),
         ("import", u"Importaciones. NCF Generado por el Sistema"),
         ("others", u"Otros. No requiere NCF"),
         ], string=u"Tipo de compra", default="normal",
        related="journal_id.purchase_type"
        )

    total_discount = fields.Monetary(
        string='Descuento', currency_field="company_currency_id",
        compute=_get_total_discount
        )

    credit_out_invoice = fields.Boolean(
        related="journal_id.credit_out_invoice"
        )

    authorize = fields.Boolean(
        u"Crédito Autorizado", default=False, copy=False)

    _sql_constraints = [
        ('number_uniq',
         'unique(number, company_id, journal_id, type, partner_id)',
         'Invoice Number must be unique per Company!'),
        ]

    @api.onchange("move_name")
    def onchange_ncf(self):
        if self.move_name and self.type in ('in_invoice', 'in_refund'):
            if not is_ncf(self.move_name, self.type):
                self.move_name = False
                return {
                    'warning': {
                            'title': u"NCF Inválido",
                            'message': u"El número de comprobante fiscal no"
                            u" es válido verifique que no está digitando un"
                            u" comprobante de Consumidor Final (Código 02)"
                            " o revise si lo ha digitado incorrectamente"
                            }
                    }
            self.invoice_ncf_validation()

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            self.currency_id = (self.journal_id.currency_id.id or
                                self.journal_id.company_id.currency_id.id)

        if self.type in ('in_invoice', 'in_refund'):
            if self.purchase_type == "normal":
                self.ncf_required = True
            else:
                self.ncf_required = False

            if not self._context.get("default_supplier", False):
                self.move_name = False

                if not self.partner_id.journal_id:
                    self.partner_id.write({"journal_id": self.journal_id.id})

                if self.purchase_type == "minor":
                    self.partner_id = (
                        self.env['res.company']._company_default_get(
                                 'account.invoice').partner_id.id)
                    self.ncf_required = False

            if self.type == "out_invoice" and self.credit_out_invoice is False:
                self.date_due = fields.Date.today()
                self.payment_term_id = 1

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        super(AccountInvoice, self)._onchange_partner_id()
        if self.type in ("in_invoice", "in_refund"):
            self.fiscal_position_id = (
                self.partner_id.property_account_position_supplier_id.id)

    @api.onchange("payment_term_id")
    def onchange_payment_term_id(self):
        if (self.payment_term_id and
                self.partner_id.property_payment_term_id.id !=
                self.payment_term_id.id):
            self.env["res.partner"].browse(self.partner_id.id).write(
                {"property_payment_term_id": self.payment_term_id.id})

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):
        if self.fiscal_position_id:
            if self.type in ('out_invoice', 'out_refund'):
                if (self.partner_id and self.partner_id.
                   property_account_position_id.id !=
                   self.fiscal_position_id.id):
                    self.partner_id.write(
                        {"property_account_position_id":
                         self.fiscal_position_id.id})

                shop_user_config = (
                    self.env["shop.ncf.config"]. get_user_shop_config())

                return {
                    "domain": {"shop_id": [('shop_id', 'in', shop_user_config[
                                            "shop_ids"])],
                               "journal_id": [('id', 'in', shop_user_config[
                                               "sale_journal_ids"])]}
                    }

            elif self.type in ('in_invoice', 'in_refund'):
                if self.partner_id.journal_id:
                    self.journal_id = self.partner_id.journal_id.id
                elif self.fiscal_position_id.journal_id:
                    self.journal_id = self.fiscal_position_id.journal_id.id

                elif self.journal_id.purchase_type == "normal":
                    self.ncf_required = True
                else:
                    self.ncf_required = False

                if (self.partner_id and
                   self.partner_id.property_account_position_supplier_id.id !=
                   self.fiscal_position_id.id):
                        self.journal_id = self.fiscal_position_id.journal_id.id
                    # self.partner_id.write(
                    #     {"property_account_position_supplier_id":
                    #      self.fiscal_position_id.id}
                    #      )

    def _check_ncf(self, rnc, ncf):
        if ncf and rnc:
            res = requests.get(
                    "http://api.marcos.do/ncf/{}/{}".format(rnc, ncf)
                    )
            if res.status_code == 200:
                return res.json()
        return {}

    @api.multi
    def invoice_ncf_validation(self):
        for invoice in self:
            if not invoice.move_name:
                invoice.move_name = self.journal_id.sequence_id.next_by_id()
        for invoice in self:
                inv_exist = self.search(
                    [('partner_id', '=', invoice.partner_id.id),
                     ('number', '=', invoice.move_name),
                     ('state', 'in', ('open', 'paid', 'cancel'))]
                    )

                if inv_exist:
                    raise exceptions.Warning(
                        u"Este número de comprobante fiscal ya se encuentra en"
                        " una factura en borrador o cancelada este proveedor")
                if (_internet_on() and
                        self.journal_id.ncf_remote_validation):
                    if invoice.journal_id.purchase_type == 'normal':
                        result = self._check_ncf(
                                        invoice.partner_id.vat,
                                        invoice.move_name)
                    result = self._check_ncf(
                                self.env.user.company_id.vat,
                                invoice.move_name)
                    if not result.get("valid", False):

                        raise exceptions.UserError(
                            u"¡El número de comprobante no es válido! No pasó"
                            u" la validación en DGII. Verifique que el NCF y"
                            u" el RNC del proveedor estén correctamente"
                            " digitados."
                            u" Si es un NCF de Proveedor Informal o de Gasto"
                            " Menor vefifique si debe solicitar números"
                            " nuevos.")
        self.signal_workflow("invoice_open")

    @api.model
    def create(self, vals):
        if not vals.get("partner_id", False):
            vals.update({"partner_id": self.env.user.company_id.partner_id.id})
        res = super(AccountInvoice, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        for rec in self:
            if rec.type in ("out_invoice", "out_refund"):
                if not vals.get("fiscal_position_id", False):
                    if not rec.fiscal_position_id:
                        fiscal_position_id = (
                         rec.env["account.fiscal.position"].
                         search([('client_fiscal_type', '=', 'final')]))
                        if not fiscal_position_id:
                            raise exceptions.ValidationError(
                                "Antes de generar una factura debe definir las"
                                " posiciones fiscales.")
                        else:
                            vals.update({"fiscal_position_id":
                                        fiscal_position_id.id})

            if rec.type in ("in_invoice", "in_refund"):
                if vals.get("purchase_type", False) == "minor":
                    vals.update({"partner_id":
                                self.env.user.company_id.partner_id.id})

        return super(AccountInvoice, self).write(vals)

    @api.model
    def _refund_cleanup_lines(self, lines):
        """ Convert records to dict of values suitable for one2many line creation
            :param recordset lines: records to convert
            :return: list of command tuple for one2many line creation
             [(0, 0, dict of values), ...]
        """
        if not lines:
            return []

        refund_type = self._context.get("refund_type", False)

        days = 0
        if lines:
            days = self.get_days_between(lines[0].invoice_id.date_invoice)

        result = []
        for line in lines:
            values = {}
            for name, field in line._fields.iteritems():
                if name in MAGIC_COLUMNS:
                    continue
                elif field.type == 'many2one':
                    values[name] = line[name].id
                elif field.type not in ['many2many', 'one2many']:
                    if name == "quantity":
                        if not refund_type:
                            values[name] = line.qty_allow_refund
                        else:
                            values["quantity"] = line[name]
                    elif name == "qty_allow_refund":
                        if not refund_type:
                            values[name] = line.qty_allow_refund
                        else:
                            values["qty_allow_refund"] = line["quantity"]
                    else:
                        values[name] = line[name]
                elif name == 'invoice_line_tax_ids':
                    if days > 30:
                        continue
                    values[name] = [(6, 0, line[name].ids)]

                values["refund_line_ref"] = line.id

            if not values:
                return []
            if lines._model == "account.invoice.line":
                if values.get("quantity", False) == 0.00:
                    continue
            result.append((0, 0, values))

        if not result:
            raise exceptions.UserError("Todos los productos de esta factura ya"
                                       " fueron devueltos.")

        return result

    @api.multi
    def invoice_validate(self):
        for rec in self:
            if rec.type in ["out_invoice", "in_invoice"]:
                for line in rec.invoice_line_ids:
                    line.qty_allow_refund = line.quantity
            elif rec.type in ["out_refund", "in_refund"]:
                for line in rec.invoice_line_ids:
                    if line.product_id:
                        if line.quantity > line.qty_allow_refund:
                            pass
                            # raise exceptions.UserError
                            # ("No puede devolver mas productos de que los\
                            # facturados.")

                    origin = self.env["account.invoice.line"].browse(
                        line.refund_line_ref.id)
                    origin.write({"qty_allow_refund": origin.qty_allow_refund -
                                 line.quantity})

                # refund_inv = self.env['account.invoice'].search([
                #     ('origin', '=', rec.number),
                #     ('state', 'in', ('open''paid'))])

                # afected_inv = self.env['account.invoice'].search([(
                #     'number', '=', rec.origin),
                #     ('state', 'in', ('open', 'paid'))])

                # total_refund = sum([
                #     rec.amount_untaxed for rec in refund_inv
                #     ]) + rec.amount_untaxed

                # amount_untaxed = sum(
                #                       [r.amount_untaxed for r in afected_inv]
                #                      ) or 0.0

                # if total_refund > amount_untaxed:
                #     raise exceptions.UserError
                #     (u"No puede crear notas de credito por un valor mayor a\
                #     la factura afectada.")

        res = super(AccountInvoice, self).invoice_validate()
        return res

    def get_days_between(self, joining_date):

        date_format = '%Y-%m-%d'
        current_date = datetime.strptime(
            datetime.today().strftime(date_format), date_format)
        doc_date = datetime.strptime(joining_date, date_format)
        delta = current_date - doc_date
        return delta.days

    @api.one
    def copy(self, default=None):
        if self.type in ("in_refund", "out_refund"):
            raise exceptions.UserError(u"¡No está permitido duplicar Notas de"
                                       u" Crédito!")
        return super(AccountInvoice, self).copy(default=default)

    @api.multi
    def authorize_credit(self):
        for rec in self:
            overdue_type = {
                'overlimit_overdue': u"Este cliente tiene el límite de"
                                     u"crédito agotado y facturas vencidas",
                'overlimit': u'Este cliente no tiene crédito disponible',
                'overdue': u'Este cliente tiene facturas vencidas',
                'none': 'None'
                }
            rec.authorize = True
            rec.message_post(body=u"<p>Crédito Autorizado con {}</p>".format
                             (overdue_type[rec.overdue_type]),
                             subject=u"Factura a Crédito Autorizada",
                             subtype="mail.mt_comment")

    @api.multi
    def disallows_credit(self):
        for rec in self:
            overdue_type = {
                'overlimit_overdue': u"Este cliente tiene el límite de"
                                     u"crédito agotado y facturas vencidas",
                'overlimit': u'Este cliente no tiene crédito disponible',
                'overdue': 'Este cliente tiene facturas vencidas',
                'none': 'None'}
            rec.authorize = False
            rec.message_post(body=u"<p>Crédito cancelado con {}</p>".
                             format(overdue_type[rec.overdue_type]),
                             subject=u"Factura a Crédito no autorizada",
                             subtype="mail.mt_comment")

    @api.multi
    def set_ncf(self):
        for inv in self:
            if (inv.type == 'out_invoice'and not inv.move_name and
               inv.journal_id.ncf_control):
                fiscal_type = inv.fiscal_position_id.client_fiscal_type
                if fiscal_type == 'fiscal':
                    sequence = inv.journal_id.fiscal_sequence_id
                elif fiscal_type == 'gov':
                    sequence = inv.journal_id.gov_sequence_id
                elif fiscal_type == 'special':
                    sequence = inv.journal_id.special_sequence_id
                elif fiscal_type == 'unico':
                    sequence = inv.journal_id.unique_sequence_id
                else:
                    sequence = inv.journal_id.final_sequence_id

                if not sequence:
                    raise exceptions.ValidationError(
                        u"Las secuencias para este diario de ventas no están"
                        " configuradas.")

                next_ncf = True
                while next_ncf:
                    ncf_next = sequence.with_context(
                        ir_sequence_date=inv.date_invoice).next_by_id()
                    if not self.search_count([('number', '=', ncf_next),
                                             ('journal_id', '=',
                                              self.journal_id.id)]):
                        _logger.info(
                            u"El Sistema Saltó el Número {} del Diario {}"
                            " porque ya Existe desde Contabilidad".format(
                             ncf_next, self.journal_id.name))
                        next_ncf = False
                inv.move_name = ncf_next


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    qty_allow_refund = fields.Float(
        string='qty allow refund',
        digits=dp.get_precision('Product Unit of Measure'),
        required=False, copy=False)

    refund_line_ref = fields.Many2one(
        "account.invoice.line", string="origin line refund", copy=False)
