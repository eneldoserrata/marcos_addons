# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2015 Marcos Organizador de Negocios SRL http://marcos.do
#    Write by Eneldo Serrata (eneldo@marcos.do)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from ..tools import is_ncf
from openerp import fields, models, api
import openerp.addons.decimal_precision as dp
from openerp import netsvc


class cjc_invoice_wizard(models.TransientModel):
    _name = "cjc.invoice.wizard"

    @api.model
    def _get_reference_type(self):
        return [('none', u'Referencia libre / Nº Fact. Proveedor'),
                ('01', '01 - Gastos de personal'),
                ('02', '02 - Gastos por trabajo, suministros y servicios'),
                ('03', '03 - Arrendamientos'),
                ('04', '04 - Gastos de Activos Fijos'),
                ('05', u'05 - Gastos de Representación'),
                ('06', '06 - Otras Deducciones Admitidas'),
                ('07', '07 - Gastos Financieros'),
                ('08', '08 - Gastos Extraordinarios'),
                ('09', '09 - Compras y Gastos que forman parte del Costo de Venta'),
                ('10', '10 - Adquisiciones de Activos'),
                ('11', '11 - Gastos de Seguro')
                ]

    @api.model
    def _get_journals(self):
        if self.env.context.get("active_model", False):
            active_model = self.pool.get("account.bank.statement").browse(self.env.cr, self.env.uid,
                                                                          self.env.context["active_id"])
            informal_journal = active_model.journal_id.informal_journal_id
            gastos_journal_id = active_model.journal_id.gastos_journal_id
            purchase_journal_id = active_model.journal_id.purchase_journal_id
            res = []
            res.append((informal_journal.id, informal_journal.name))
            res.append((gastos_journal_id.id, gastos_journal_id.name))
            res.append((purchase_journal_id.id, purchase_journal_id.name))
            if len(res) != 3:
                raise models.except_orm('Configuracion pendiente!',
                                        "Se deben configurar los diarios para este tipo de docuemnto.")
            return tuple(res)


    company_id = fields.Many2one('res.company', 'Company', default=1)
    partner_id = fields.Many2one("res.partner", "Proveedor")
    reference_type = fields.Selection(_get_reference_type, "Tipo de comprobante", required=True)
    date = fields.Date("Fecha", required=True, default=fields.Date.context_today)
    concept = fields.Char("Concepto", required=True)
    ncf = fields.Char("NCF", size=19)
    journal_id = fields.Many2one("account.journal", "Diario de compra",
                                 domain=[('ncf_special', 'in', ('gasto', 'informal', 'pruchase'))], required=True)
    line_ids = fields.One2many("cjc.invoice.line.wizard", "invoice_id", "Productos", select=False, required=True,
                               ondelete='cascade')
    ncf_requierd = fields.Boolean("NCF Requerido.", default=False)
    ncf_minor = fields.Boolean(default=False)


    @api.onchange("journal_id")
    def onchange_journal(self):
        if self.journal_id:
            self.ncf_requierd = True
            self.ncf_minor = False
            if self.journal_id.ncf_special in ['gasto', 'informal']:
                self.ncf_requierd = False
                if self.journal_id.special_partner:
                    self.ncf_minor = True
                    self.partner_id = self.journal_id.special_partner.id


    @api.model
    def _parse_vals(self, current_model):
        vals = {}
        for inv in self:
            journal_obj = self.env["account.journal"].browse(int(inv.journal_id))

            if not journal_obj.default_credit_account_id.id:
                raise models.except_orm('Configuracion pendiente!', "Se deben configurar las cuentas para este diario.")
            elif not inv.line_ids:
                raise models.except_orm('Registro sin productos!', "Debe de registrar por lo menos un producto.")

            ncf_required = True
            if journal_obj.ncf_special in ['gasto', 'informal']:
                ncf_required = False
            if ncf_required and not is_ncf(inv.ncf.encode("ascii")):
                raise models.except_orm(u"NCF Invalido!", u"El NCF del proveedor no es válido!")


            vals.update({
                u'account_id': current_model.journal_id.default_credit_account_id.id,
                u'check_total': 0,
                u'child_ids': [[6, False, []]],
                u'comment': "Factura de caja chica",
                u'company_id': inv.company_id.id,
                u'currency_id': journal_obj.company_id.currency_id.id,
                u'date_due': False,
                u'date_invoice': self.date,
                u'fiscal_position': self.partner_id.property_account_position.id,
                u'internal_number': self.ncf,
                u'journal_id': int(self.journal_id.id),
                u'message_follower_ids': False,
                u'message_ids': False,
                u'name': False,
                u'ncf_required': ncf_required,
                u'origin': current_model.name,
                u'parent_id': False,
                u'partner_bank_id': False,
                u'partner_id': self.partner_id.id or self.journal_id.special_partner.id,
                u'payment_term': False,
                u'period_id': current_model.period_id.id,
                u'reference': self.ncf,
                u'reference_type': self.reference_type,
                u'supplier_invoice_number': False,
                u'tax_line': [],
                u'user_id': self.env.uid,
                u'pay_to': current_model.journal_id.pay_to.id,
                u'invoice_line': []
            })

            for line in inv.line_ids:
                line_list = [0, False]
                line_dict = {}
                line_dict.update({
                    u'account_analytic_id': False,
                    u'asset_category_id': False,
                    u'discount': 0,
                    u'invoice_line_tax_id': [[6, False, [t.id for t in line.concept_id.supplier_taxes_id]]],
                    u'name': line.concept_id.name,
                    u'price_unit': abs(line.amount),
                    # u'product_id': line.concept_id.product_id.id,
                    u'quantity': 1,
                    u'uos_id': 1
                })
                line_list.append(line_dict)
                vals["invoice_line"].append(line_list)

        context = {u'default_type': u'in_invoice', u'journal_type': u'purchase'}

        result = self.env["account.invoice"].with_context(context).create(vals)
        return result

    @api.multi
    def create_purchase(self):

        current_model = self.pool.get(self.env.context['active_model']).browse(self.env.cr, self.env.uid, self.env.context['active_id'])
        purchase_invoice_id = self._parse_vals(current_model)

        inv = self.env["account.invoice"].browse(purchase_invoice_id.id)
        inv.check_total = inv.amount_total

        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(self.env.uid, 'account.invoice', inv.id, 'invoice_open', self.env.cr)

        lines_vals = {u'account_id': current_model.journal_id.default_debit_account_id.id,
                      u'amount': inv.amount_total * -1,
                      u'analytic_account_id': False,
                      u'date': inv.date_invoice,
                      u'name': self.concept,
                      u'partner_id': self.partner_id.id or self.journal_id.special_partner.id,
                      u'ref': inv.number,
                      u'sequence': 0,
                      u'statement_id': current_model.id,
                      u'type': u'supplier',
                      u'voucher_id': False,
                      u"invoice_id": inv.id,
                      u"journal_id": current_model.journal_id.id

                      }
        self.pool.get('account.bank.statement.line').create(self.env.cr, self.env.uid, lines_vals, context=self.env.context)
        return {'type': 'ir.actions.act_window_close'}


class cjc_invoice_line_wizard(models.TransientModel):
    _name = "cjc.invoice.line.wizard"

    concept_id = fields.Many2one("cjc.concept", "Conceptos", required=True)
    amount = fields.Float('Amount', digits_compute=dp.get_precision('Account'), required=True, default=1)
    invoice_id = fields.Many2one("cjc.invoice.wizard", "Factura", ondelete='cascade', select=True)