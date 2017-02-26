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
from openerp import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _default_user_shop(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        return shop_user_config

    shop_id = fields.Many2one("shop.ncf.config", string="Sucursal",
                              required=False, default=_default_user_shop,
                              domain=lambda s: [('user_ids', '=', [s._uid])])
    ncf_required = fields.Boolean(copy=True)

    ncf_control = fields.Boolean(related="journal_id.ncf_control")

    sale_fiscal_type = fields.Selection(
                            related="fiscal_position_id.sale_fiscal_type")

    expense_type = fields.Selection(
        [('01', u'01 - Gastos de Personal'),
         ('02', u'02 - Gastos por Trabajo, Suministros y Servicios'),
         ('03', u'03 - Arrendamientos'),
         ('04', u'04 - Gastos de Activos Fijos'),
         ('05', u'05 - Gastos de Representación'),
         ('06', u'06 - Otras Deducciones Admitidas'),
         ('07', u'07 - Gastos Financieros'),
         ('08', u'08 - Gastos Extraordinarios'),
         ('09', u'09 - Compras y Gastos que forman parte del Costo de Venta'),
         ('10', u'10 - Adquisiciones de Activos'),
         ('11', u'11 - Gastos de Seguro')],
        string=u"Tipo de gasto")

    purchase_fiscal_type = fields.Selection(related="journal_id.purchase_fiscal_type")

    pay_to = fields.Many2one("res.partner", string="Pagar a",
                             readonly=True,
                             states={'draft': [('readonly', False)]},
                             copy=False)

    charge_to = fields.Many2one("res.partner", string="Facturar a",
                                readonly=True,
                                states={'draft': [('readonly', False)]},
                                copy=False)

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

    @api.onchange("shop_id")
    def onchange_shop_id(self):
        self.journal_id = self.shop_id.journal_id

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.type in ('in_invoice', 'in_refund'):
            if self.purchase_fiscal_type == "normal":
                self.ncf_required = True
            else:
                self.ncf_required = False

            if not self._context.get("default_supplier", False):
                self.move_name = False

                if not self.partner_id.journal_id:
                    self.partner_id.write({"journal_id": self.journal_id.id})

                if self.purchase_fiscal_type == "minor":
                    self.partner_id = (
                        self.env['res.company']._company_default_get(
                                 'account.invoice').partner_id.id)
                    self.ncf_required = False

    @api.onchange('partner_id')
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

            elif self.type in ('in_invoice', 'in_refund'):
                if self.partner_id.journal_id:
                    self.journal_id = self.partner_id.journal_id.id
                elif self.fiscal_position_id.journal_id:
                    self.journal_id = self.fiscal_position_id.journal_id.id

                elif self.journal_id.purchase_fiscal_type == "normal":
                    self.ncf_required = True
                else:
                    self.ncf_required = False

                if (self.partner_id and
                   self.partner_id.property_account_position_supplier_id.id !=
                   self.fiscal_position_id.id):
                        self.journal_id = self.fiscal_position_id.journal_id.id

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
                        u"El número de comprobante fiscal {} ya se encuentra"
                        " registrado con este mismo proveedor en una factura"
                        " en borrador o cancelada".format(invoice.move_name))
                if (_internet_on() and
                        self.journal_id.ncf_remote_validation):
                    if invoice.journal_id.purchase_fiscal_type == 'normal':
                        result = self._check_ncf(
                                                 invoice.partner_id.vat,
                                                 invoice.move_name)
                        if result.get("valid", False) is False:
                            raise exceptions.UserError(
                                u"¡El número de comprobante {} del proveedor"
                                u" {} no es válido! No pasó la validación en"
                                u" DGII. Verifique que el NCF y el RNC del"
                                u"proveedor estén correctamente"
                                u"digitados.".format(
                                                     invoice.move_name,
                                                     invoice.partner_id.vat))
                    else:
                        result = self._check_ncf(
                                self.env.user.company_id.vat,
                                invoice.move_name)
                        if result.get("valid", False) is False:
                            raise exceptions.UserError(
                                u"¡El número de comprobante {} no es válido."
                                u" No pasó la validación en DGII.\n\n"
                                u" Si es un NCF de Proveedor Informal o de"
                                u" Gasto Menor vefifique si debe solicitar"
                                u" números nuevos.".format(invoice.move_name))

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
                if self._context.get("active_model", False) == "sale.order":
                    vals.update({"fiscal_position_id": rec.partner_id.property_account_position_id.id})
                else:
                    if not vals.get("fiscal_position_id", False):
                        if not rec.fiscal_position_id:
                            fiscal_position_id = rec.env["account.fiscal.position"].search(
                                [('sale_fiscal_type', '=', 'final')])
                            if not fiscal_position_id:
                                raise exceptions.ValidationError(
                                    "Antes de generar una factura debe definir"
                                    " las posiciones fiscales.")
                            else:
                                vals.update(
                                    {"fiscal_position_id":
                                     fiscal_position_id.id})
            if rec.type in ("in_invoice", "in_refund"):
                if vals.get("purchase_fiscal_type", False) == "minor":
                    vals.update({"partner_id":
                                self.env.user.company_id.partner_id.id})

        return super(AccountInvoice, self).write(vals)

    @api.one
    def copy(self, default=None):
        if self.type in ("in_refund", "out_refund"):
            raise exceptions.UserError(u"¡No está permitido duplicar Notas de"
                                       u" Crédito!")
        return super(AccountInvoice, self).copy(default=default)
