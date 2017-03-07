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
from odoo import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _default_user_shop(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        return shop_user_config

    shop_id = fields.Many2one("shop.ncf.config", string=u"Prefijo NCF",
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

    purchase_fiscal_type = fields.Selection(
                            related="journal_id.purchase_fiscal_type")

    anulation_type = fields.Selection(
        [("01", u"01 - Deterioro de Factura Pre-impresa"),
         ("02", u"02 - Errores de Impresión (Factura Pre-impresa)"),
         ("03", u"03 - Impresión Defectuosa"),
         ("04", u"04 - Duplicidad de Factura"),
         ("05", u"05 - Corrección de La Información"),
         ("06", u"06 - Cambio de Productos"),
         ("07", u"07 - Devolución de Productos"),
         ("08", u"08 - Omisión de Productos"),
         ("09", u"09 - Errores en Secuencia de NCF")],
        string=u"Tipo de anulación", copy=False)

    refund_reason = fields.Text(string="Refund reason")
    origin_invoice_ids = fields.Many2many(
        comodel_name='account.invoice', column1='refund_invoice_id',
        column2='original_invoice_id', relation='account_invoice_refunds_rel',
        string=u"Factura original", readonly=True,
        help=u"Factura original a la que se remite esta factura de reembolso")
    refund_invoice_ids = fields.Many2many(
        comodel_name='account.invoice', column1='original_invoice_id',
        column2='refund_invoice_id', relation='account_invoice_refunds_rel',
        string=u"Reembolso de facturas", readonly=True,
        help=u"Devolución de facturas creadas a partir de esta factura")

    @api.multi
    def match_origin_lines(self, origin_inv):
        for idx, line in enumerate(origin_inv.invoice_line_ids):
            try:
                # Protect this write, maybe refund invoice doesn't
                # have the same lines than original one
                self.invoice_line_ids[idx].write({
                    'origin_line_ids': [(6, 0, line.ids)],
                })
            except:  # pragma: no cover
                pass
        return True

    is_nd = fields.Boolean()

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        super(AccountInvoice, self)._onchange_journal_id()

        if self.journal_id.type == 'purchase':
            if self.journal_id.purchase_fiscal_type == "normal":
                self.ncf_required = True
            else:
                self.ncf_required = False

            if self.journal_id.purchase_type == "minor":
                self.partner_id = self.company_id.partner_id.id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super(AccountInvoice, self)._onchange_partner_id()

        if self.partner_id:
            if self.type in ['out_invoice', 'out_refund']:
                self.sale_fiscal_type = self.partner_id.sale_fiscal_type
            else:
                self.expense_type = self.partner_id.expense_type

            if self.journal_id.type == 'purchase' and self.journal_id.purchase_fiscal_type == "minor":
                self.partner_id = self.company_id.partner_id.id

            if self.type in ["out_invoice", "out_refund"] and not self.partner_id.customer:
                self.partner_id.customer = True
            if self.type in ["in_invoice", "in_refund"] and not self.partner_id.supplier:
                self.partner_id.supplier = True

    @api.onchange('sale_fiscal_type', 'expense_type')
    def _onchange_fiscal_type(self):
        if self.partner_id:
            if self.type in ['out_invoice', 'out_refund']:
                self.partner_id.write(
                                {'sale_fiscal_type': self.sale_fiscal_type})
                if self.sale_fiscal_type == "special":
                    self.fiscal_position_id = self.env.ref(
                            "ncf_manager.ncf_manager_special_fiscal_position")
            else:
                self.partner_id.write({'expense_type': self.expense_type})

    @api.onchange("shop_id")
    def onchange_shop_id(self):
        if self.type in ['out_invoice', 'out_refund']:
            self.journal_id = self.shop_id.journal_id.id

    @api.one
    @api.constrains("move_name")
    def constrains_move_name(self):
        if self.type in ("in_invoice", "in_refund"):
            res = self.env["marcos.api.tools"].invoice_ncf_validation(self)
            if res is not True:
                _logger.warning(res)
                raise exceptions.ValidationError(res[2])

    @api.multi
    def action_invoice_open(self):
        msg = False
        for rec in self:
            if (rec.type in ("out_invoice", "out_refund") and
               rec.journal_id.ncf_control and
               rec.sale_fiscal_type != "final" and not rec.partner_id.vat):
                msg = u"¡Para este tipo de Posición Fiscal el Cliente"
                u" debe de tener un RNC/Cédula establecido!"

            elif (rec.type in ("in_invoice", "in_refund") and
                  rec.journal_id.purchase_fiscal_type == "normal" and
                  not rec.partner_id.vat):
                msg = u"El Proveedor no tiene RNC y es requerido para este"
                " tipo de compra."

            if msg:
                raise exceptions.ValidationError(msg)

        return super(AccountInvoice, self).action_invoice_open()

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):
        if self.fiscal_position_id:
            if self.type in ['out_invoice', 'out_refund']:
                if (self.partner_id and self.partner_id.
                   property_account_position_id.id !=
                   self.fiscal_position_id.id):
                    self.partner_id.write(
                        {"property_account_position_id":
                         self.fiscal_position_id.id})

            elif self.type in ['in_invoice', 'in_refund']:
                if self.fiscal_position_id.journal_id:
                    self.journal_id = self.fiscal_position_id.journal_id.id

                if (self.partner_id and
                   self.partner_id.property_account_position_supplier_id.id !=
                   self.fiscal_position_id.id):
                        self.journal_id = self.fiscal_position_id.journal_id.id

    @api.one
    def copy(self, default=None):
        if self.type in ["in_refund", "out_refund"]:
            raise exceptions.UserError(u"¡No está permitido duplicar Notas de"
                                       u" Crédito!")
        return super(AccountInvoice, self).copy(default=default)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    origin_line_ids = fields.Many2many(
        comodel_name='account.invoice.line', column1='refund_line_id',
        column2='original_line_id', string=u"Línea de factura original",
        relation='account_invoice_line_refunds_rel',
        help=u"Línea de factura original a la que se refiere esta línea de factura de reembolso")
    refund_line_ids = fields.Many2many(
        comodel_name='account.invoice.line', column1='original_line_id',
        column2='refund_line_id', string=u"Reembolso de la línea de factura",
        relation='account_invoice_line_refunds_rel',
        help=u"Reembolso de las líneas de factura creadas a partir de esta línea de factura")
