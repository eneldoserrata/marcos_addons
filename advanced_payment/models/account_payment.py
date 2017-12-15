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

from odoo import models, fields, api, exceptions, _, release

import textwrap

import logging

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'mail.thread', 'ir.needaction_mixin', 'utm.mixin']

    @api.one
    @api.depends("currency_id")
    def _check_is_base_currency(self):
        self.is_base_currency = self.currency_id.id == self.company_id.currency_id.id

    @api.one
    @api.depends("payment_invoice_ids.move_line_id",
                 "payment_invoice_ids.currency_id",
                 "payment_invoice_ids.payment_compute_auto",
                 "payment_invoice_ids.amount_currency_pay",
                 "payment_invoice_ids.amount",
                 "payment_invoice_ids.invoice_rate",
                 )
    def _calc_payment_amount(self):

        if self.move_type == "invoice" and self.payment_invoice_ids:
            # Filter only invoice line with psy amount
            payment_invoice_ids = self.payment_invoice_ids.filtered(lambda x: x.amount > 0)
            if payment_invoice_ids:

                self.amount_currency = 0
                self.payment_amount = 0
                self.currency_diff = 0

                # collect all currency_id from invoice line
                for inv in payment_invoice_ids:

                    currency_id = inv.currency_id
                    payment_compute_auto = inv.payment_compute_auto
                    amount_currency_pay = inv.amount_currency_pay
                    amount = inv.amount
                    invoice_rate = inv.invoice_rate

                    # compute payment in second currency
                    if payment_compute_auto:
                        self.amount_currency += amount_currency_pay
                    else:
                        if invoice_rate > 0:
                            self.amount_currency += amount / invoice_rate

                    # Total a pagar en moneda local a la tasa de la trasaccion
                    if self.amount_currency:
                        if payment_compute_auto:
                            self.payment_amount += amount_currency_pay * invoice_rate
                        else:
                            self.payment_amount += amount
                    else:
                        self.payment_amount += amount

                if self.amount_currency:
                    if self.currency_id == self.rate_currency_id:
                        self.currency_diff = self.payment_amount - (self.amount*self.rate)
                    else:
                        self.currency_diff = self.payment_amount - self.amount
                    # muestra el tipo de diferencia cambiaria
                    if self.currency_diff > 0:
                        self.currency_diff_type = "out" if self.payment_type == "inbound" else "in"
                    elif self.currency_diff < 0:
                        self.currency_diff_type = "in" if self.payment_type == "inbound" else "out"
                    elif self.currency_diff == 0:
                        self.currency_diff_type = "none"

    move_type = fields.Selection([('auto', 'Automatic'), ('manual', 'Manual'), ('invoice', 'Pay bills')],
                                 string=u"Forma de pago",
                                 default="auto", required=True, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('request', 'Solicitud'), ('posted', 'Posted'), ('sent', 'Sent'),
                              ('reconciled', 'Reconciled'), ("null", "Anulado")], readonly=True, default='draft',
                             copy=False,
                             string="Status")
    payment_move_ids = fields.One2many("payment.move.line", "payment_id", copy=False)
    payment_invoice_ids = fields.One2many("payment.invoice.line", "payment_id", copy=False)
    rate = fields.Float("Tasa", digits=(12, 6))

    currency_diff_type = fields.Selection(
        [('in', 'INGRESO POR DIFERENCIA CAMBIARIA'), ('out', 'GASTO POR DIFERENCIA CAMBIARIA'),
         ("none", "SIN DIFERENCIA CAMBIARIA")], compute="_calc_payment_amount", string=u"Tipo de diferencia")
    rate_currency_id = fields.Many2one("res.currency", string=u"Divisa de facturas", search=[('id','!=',lambda x: x.env.user.company_id.currency_id.id)])

    amount_currency = fields.Float(u"Pago(s)", compute="_calc_payment_amount", digits=(12, 6))

    payment_amount = fields.Monetary(u"Inporte a la fecha de la trasacción", compute="_calc_payment_amount")

    currency_diff = fields.Monetary(u"Diferencia cambiaria", compute="_calc_payment_amount")

    is_base_currency = fields.Boolean(compute="_check_is_base_currency")
    invoice_payemnt_discount = fields.Char(u"Descuento",
                                           help=u"Este descuento se aplica al subtotal y no afecta el impuesto"
                                                u"tambien puede colocar varios descuentos separados por una coma en los casos"
                                                u"que sea un 5% de descuento y luego un 3% que puede ocurrir"
                                                u"en algunos casos.")

    @api.one
    def amount_total(self, update_communication=True):
        lines_amount = 0
        currency_set = set()
        if update_communication:
            self.communication = "PAGO A FACTUTA(S)"

        payment_invoice_ids = self.payment_invoice_ids.filtered(lambda x: x.amount > 0)
        for line in payment_invoice_ids:
            currency_set.add(line.currency_id.id)
            lines_amount += line.amount

            if update_communication:
                self.communication += " {},".format(str(line.move_line_id.name_get()[0][1]))

        if self.rate_currency_id:
            if self.currency_id == self.rate_currency_id:
                self.amount = self.amount_currency
            else:
                self.amount = self.amount_currency * self.rate
        else:
            self.amount = lines_amount

        if len(currency_set) > 1:
            self.amount = 0
            raise exceptions.ValidationError(
                u"No puede pagar facturas en monedas diferentes para un solo pago.")

    @api.multi
    def _create_payment_entry_manual(self, amount):

        if self._context.get("active_model", False) == "account.invoice":
            return super(AccountPayment, self)._create_payment_entry_manual(amount)

        manual_debit = round(sum([line.debit for line in self.payment_move_ids]), 2)
        manual_credit = round(sum([line.credit for line in self.payment_move_ids]), 2)
        if manual_credit != manual_debit:
            raise exceptions.UserError(_("You can not create journal entry that is not square."))

        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        debit, credit, amount_currency, currency_id = aml_obj.with_context(
            date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id,
                                                          invoice_currency)

        move = self.env['account.move'].create(self._get_move_vals())

        # Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})

        account_id = self.payment_type in ('outbound',
                                           'transfer') and self.journal_id.default_debit_account_id.id or self.journal_id.default_credit_account_id.id,
        manual_lines = [line for line in self.payment_move_ids if line.account_id.id not in account_id]
        rate = False
        if counterpart_aml_dict.get("amount_currency", False):
            rate = counterpart_aml_dict["debit"] / counterpart_aml_dict["amount_currency"] if counterpart_aml_dict[
                                                                                                  "debit"] > 0 else \
                counterpart_aml_dict["credit"] / counterpart_aml_dict["amount_currency"]
        for line in manual_lines:

            line_amount_currency = False
            line_debit = line.debit
            line_credit = line.credit
            if rate:
                line_amount_currency = line.debit if line.debit else line.credit
                if self.payment_type == "inbound":
                    line_amount_currency = line_amount_currency * -1
                line_debit = line_debit * rate
                line_credit = line_credit * rate

            line_dict = {'account_id': line.account_id.id,
                         'amount_currency': line_amount_currency,
                         'credit': abs(line_credit),
                         'currency_id': counterpart_aml_dict["currency_id"],
                         'debit': abs(line_debit),
                         'invoice_id': counterpart_aml_dict["invoice_id"],
                         'journal_id': counterpart_aml_dict["journal_id"],
                         'move_id': counterpart_aml_dict["move_id"],
                         'name': line.name or counterpart_aml_dict["name"],
                         'partner_id': line.partner_id.id if line.partner_id else counterpart_aml_dict["partner_id"],
                         'product_id': line.product_id.id,
                         'analytic_account_id': line.analytic_account_id.id,
                         'payment_id': counterpart_aml_dict["payment_id"]}
            aml_obj.create(line_dict)

        # Write counterpart lines
        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0
        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))

        aml_obj.create(liquidity_aml_dict)

        return move

    @api.multi
    def _create_payment_entry_invoice(self):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """

        currency_diff = self.currency_diff

        payment_invoice_ids = self.payment_invoice_ids

        # add invoice to payment
        self.invoice_ids = self.env["account.invoice"].browse(
            [m_line.move_line_id.invoice_id.id for m_line in payment_invoice_ids])

        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)

        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id

        debit, credit, amount_currency, currency_id = aml_obj.with_context(
            date=self.payment_date).compute_amount_fields(self.amount, self.currency_id, self.company_id.currency_id,
                                                          invoice_currency)

        move = self.env['account.move'].create(self._get_move_vals())

        for inv in payment_invoice_ids:

            credit = inv.amount if self.payment_type == "inbound" else 0
            debit = inv.amount if self.payment_type == "outbound" else 0

            counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id,
                                                                   inv.move_line_id.invoice_id)
            # TODO FAST FIX because some company partner do not get find_accounting_partner have to check this
            if not counterpart_aml_dict.get("partner_id", False):
                counterpart_aml_dict.update({"partner_id": self.partner_id.id})
            # ENDTODO

            # Write line corresponding to invoice payment
            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(inv.move_line_id.invoice_id))
            counterpart_aml_dict.update({'currency_id': currency_id})

            if inv.currency_id:
                if credit > 0:
                    counterpart_aml_dict.update({"amount_currency": abs(inv.amount / inv.invoice_rate) * -1,
                                                 "currency_id": inv.currency_id.id})
                else:
                    counterpart_aml_dict.update({"amount_currency": abs(inv.amount / inv.invoice_rate),
                                                 "currency_id": inv.currency_id.id})
            else:
                counterpart_aml_dict.update({"amount_currency": False,
                                             "currency_id": False})

            counterpart_aml = aml_obj.create(counterpart_aml_dict)

            inv.move_line_id.invoice_id.register_payment(counterpart_aml)

        # Write counterpart lines
        liquidity_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(self.amount))

        if self.rate_currency_id == self.currency_id:
            debit = self.currency_id.round(self.amount * self.rate) if self.payment_type == "inbound" else 0
            credit = self.currency_id.round(self.amount * self.rate) if self.payment_type == "outbound" else 0
        else:
            debit = self.amount if self.payment_type == "inbound" else 0
            credit = self.amount if self.payment_type == "outbound" else 0


        if debit > 0:
            amount_currency = self.amount_currency
        else:
            amount_currency = self.amount_currency * -1

        liquidity_aml_dict.update({"debit": debit,
                                   "credit": credit,
                                   "partner_id": self.partner_id.id,
                                   "currency_id": self.rate_currency_id.id if self.rate_currency_id else False,
                                   "amount_currency": amount_currency,
                                   })
        aml_obj.create(liquidity_aml_dict)

        if not liquidity_aml_dict.get("account_id", False):
            raise exceptions.ValidationError("De diario de pago no tiene cuenta asignada.")

        if currency_diff:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            if not self.company_id.currency_exchange_journal_id:
                raise exceptions.ValidationError(u"Debe de configurar el diario para diferencias cambiarias")

            writeoff_debit_account_id = self.company_id.currency_exchange_journal_id.default_debit_account_id
            writeoff_credit_account_id = self.company_id.currency_exchange_journal_id.default_credit_account_id

            if not writeoff_debit_account_id or not writeoff_credit_account_id:
                raise exceptions.ValidationError(u"Las cuentas para diferencias cambiarias no estan configuradas.")

            if currency_diff < 0:
                writeoff_line['account_id'] = writeoff_debit_account_id.id
                writeoff_line['debit'] = abs(currency_diff)
                writeoff_line['credit'] = 0
                writeoff_line['amount_currency'] = (currency_diff / self.rate) * -1
            elif currency_diff > 0:
                writeoff_line['account_id'] = writeoff_credit_account_id.id
                writeoff_line['debit'] = 0
                writeoff_line['credit'] = abs(currency_diff)
                writeoff_line['amount_currency'] = (currency_diff / self.rate) * -1

            writeoff_line['name'] = _('Diferencia cambiaria')
            writeoff_line['currency_id'] = self.rate_currency_id.id if self.rate_currency_id else False
            writeoff_line['payment_id'] = self.id
            writeoff_line['partner_id'] = self.partner_id.id
            aml_obj.create(writeoff_line)

        move.post()
        return move

    def set_payment_name(self):

        if self.state not in ('draft', 'request'):
            raise exceptions.UserError(
                _("Only a draft payment can be posted. Trying to post a payment in state %s.") % self.state)

        if any(inv.state != 'open' for inv in self.invoice_ids):
            raise exceptions.ValidationError(_("The payment cannot be processed because the invoice is not open!"))

        if not self.name or self.name == "Draft Payment":
            if self.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if self.partner_type == 'customer':
                    if self.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if self.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if self.partner_type == 'supplier':
                    if self.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if self.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.payment_date).next_by_code(
                sequence_code)

    @api.multi
    def action_receipt_sent(self):

        self.ensure_one()
        template = self.env.ref('advanced_payment.email_template_edi_payment_order', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.payment',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def mail_post(self):
        if self.partner_id.email and self.partner_id.send_payment_order:
            template_id = self.env.ref('advanced_payment.email_template_edi_payment_order')
            mail_id = template_id.send_mail(self.id, True,
                                            email_values={"email_to": self.partner_id.email, "partner_ids": []})
            return True

    @api.multi
    def post(self):

        if self._context.get("active_model", False) == "account.invoice":
            return super(AccountPayment, self).post()

        for rec in self:
            if rec.move_type == "auto":
                # Create the journal entry
                amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
                move = rec._create_payment_entry(amount)
                if rec.payment_type == 'transfer':
                    transfer_credit_aml = move.line_ids.filtered(
                        lambda r: r.account_id == rec.company_id.transfer_account_id)
                    transfer_debit_aml = rec._create_transfer_entry(amount)
                    (transfer_credit_aml + transfer_debit_aml).reconcile()
                rec.state = 'posted'
            elif rec.move_type == "manual":
                amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
                rec._create_payment_entry_manual(amount)
                rec.state = 'posted'
            elif rec.move_type == "invoice":
                amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and -1 or 1)
                rec._create_payment_entry_invoice()
                rec.state = 'posted'
        self.mail_post()

    @api.multi
    def payment_request(self):
        for rec in self:
            if rec.amount == 0:
                raise exceptions.ValidationError("No puede solicitar un pago valor 0.")

            if rec.move_type == "auto":
                rec.state = 'request'
            elif rec.move_type == "manual":

                payment_account = rec.journal_id.default_debit_account_id.id

                if self.payment_type == "inbound":
                    payment_account_amount = sum(
                        [deb.debit for deb in rec.payment_move_ids if deb.account_id.id == payment_account])
                else:
                    payment_account_amount = sum(
                        [cre.credit for cre in rec.payment_move_ids if cre.account_id.id == payment_account])

                if round(payment_account_amount, 2) != round(rec.amount, 2):
                    raise exceptions.ValidationError("El monto del pago no coincide con la suma de los apuntes.")

                debits = sum([deb.debit for deb in rec.payment_move_ids])
                credits = sum([cre.credit for cre in rec.payment_move_ids])

                if round(debits, 2) - round(credits, 2) != 0:
                    raise exceptions.ValidationError("El asiento manual no esta cuadrado.")

                rec.state = 'request'
            elif rec.move_type == "invoice":

                no_payment_invoice_ids = self.payment_invoice_ids.filtered(lambda x: x.amount == 0)
                no_payment_invoice_ids.unlink()
                payment_invoice_ids = self.payment_invoice_ids.filtered(lambda x: x.amount > 0)

                for inv_line in payment_invoice_ids:
                    for line in inv_line.move_line_id.move_id.line_ids:
                        if not line.partner_id:
                            line.partner_id = self.partner_id.id

                rec.amount_total(update_communication=False)

                if not payment_invoice_ids:
                    raise exceptions.ValidationError("Debe espesificar los montos a pagar por facturas.")

                currency_ids = set()

                if len(currency_ids) > 1 and not self.rate_currency_id:
                    raise exceptions.ValidationError(
                        "Para pagar una factura registrada en otra moneda debe indicar el tipo de divisa su importe y tasa.")

                rec.state = 'request'
            rec.set_payment_name()

    @api.multi
    def reset_move_type(self):
        self.payment_invoice_ids = False
        self.amount = 0
        self.move_type = 'auto'

    @api.onchange("partner_id", "invoice_payemnt_discount")
    def _onchange_partner_id(self):
        self.reset_move_type()

    @api.onchange("currency_id")
    def onchange_currency_id(self):
        self.reset_move_type()

        if not self.is_base_currency:
            ctx = dict(self._context)
            if self.payment_date:
                ctx.update({"date": self.payment_date})

            rate = self.currency_id.with_context(ctx).rate
            if rate:
                self.rate = 1 / self.currency_id.with_context(ctx).rate
            else:
                view_id = self.env.ref("currency_rates_control.update_rate_wizard_form", True)
                return {
                    'name': _('Fecha sin tasa, Actualizar tasa de la moneda'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'update.rate.wizard',
                    'view_id': view_id.id,
                    'target': 'new',
                    'views': False,
                    'type': 'ir.actions.act_window',
                    'context': {"default_name": self.payment_date or fields.Date.today()}
                }

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        self.reset_move_type()
        return super(AccountPayment, self)._onchange_payment_type()

    @api.onchange('journal_id')
    def _onchange_journal(self):
        self.reset_move_type()
        return super(AccountPayment, self)._onchange_journal()

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        self.reset_move_type()
        return super(AccountPayment, self)._onchange_partner_type()

    @api.onchange("move_type")
    def onchange_move_type(self):
        self.payment_invoice_ids = False
        self.amount = 0
        if self.move_type == "manual":
            self.rate_currency_id = False
            if self.journal_id:
                if self.payment_type == "outbound":
                    first_move = self.env["payment.move.line"].create(
                        {"account_id": self.journal_id.default_credit_account_id.id, "credit": self.amount})
                    self.payment_move_ids = first_move

                elif self.payment_type == "inbound":
                    first_move = self.env["payment.move.line"].create(
                        {"account_id": self.journal_id.default_debit_account_id.id, "debit": self.amount})
                    self.payment_move_ids = first_move

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0 and self.state != "draft":
            raise exceptions.ValidationError(_('The payment amount must be strictly positive.'))

    @api.multi
    def update_invoice(self):
        self.communication = False
        for rec in self:
            rec.payment_invoice_ids.unlink()

        if not self.journal_id:
            raise exceptions.ValidationError("Seleccione el meétodo de pago")
        for rec in self:
            journal_type = 'purchase' if rec.payment_type == "outbound" else 'sale'
            invoice_type = 'in_invoice' if rec.payment_type == "outbound" else 'out_invoice'
            if not rec.partner_id:
                rec.move_type = "auto"
                return {
                    'value': {"move_type": "auto"},
                    'warning': {'title': "Warning", 'message': _("You must first select a partner.")},
                }

            if not self.rate_currency_id:
                currency_id = self.currency_id
            else:
                currency_id = self.rate_currency_id

            open_invoice = self.env["account.invoice"].search([('state', '=', 'open'),
                                                               ('pay_to', '=', rec.partner_id.id),
                                                               ('currency_id', '=', currency_id.id),
                                                               ('journal_id.type', '=', journal_type),
                                                               ('type', '=', invoice_type)])

            open_invoice |= self.env["account.invoice"].search([('state', '=', 'open'),
                                                                ('partner_id', '=', rec.partner_id.id),
                                                                ('currency_id', '=', currency_id.id),
                                                                ('journal_id.type', '=', journal_type),
                                                                ('pay_to', '=', False),
                                                                ('type', '=', invoice_type)])

            inv_ids = [inv.id for inv in open_invoice]
            if inv_ids == []:
                return {
                    'value': {"move_type": "auto"},
                    'warning': {'title': "Warning", 'message': _("No existen facturas pendientes.")},
                }
            rows = self.env['account.move.line'].search([('invoice_id', 'in', inv_ids),
                                                         ('account_id.reconcile', '=', True),
                                                         ('reconciled', '=', False)])

            for row in rows:
                if not row.partner_id:
                    self.env["account.move.line"].search([('move_id', '=', row.move_id.id)]).write(
                        {"partner_id": rec.partner_id.id})

                rec.payment_invoice_ids.create({'move_line_id': row.id, "payment_id": rec.id})

    @api.multi
    def pay_all(self):
        self.communication = False
        self.payment_invoice_ids.full_pay()

    @api.multi
    def unpay_all(self):
        self.communication = False
        self.payment_invoice_ids.unfull_pay()

    @api.multi
    def payment_request_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'advanced_payment.payment_request_report_doc')

    @api.model
    def create(self, vals):
        currency_id = vals.get("currency_id")
        if currency_id != self.env.user.company_id.currency_id.id:
            vals.update({"rate_currency_id": self.env.user.company_id.currency_id.id})
        return super(AccountPayment, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("currency_id", False):
            currency_id = vals.get("currency_id")
            if currency_id != self.env.user.company_id.currency_id.id:
                vals.update({"rate_currency_id": self.env.user.company_id.currency_id.id})
        return super(AccountPayment, self).write(vals)

    @api.multi
    def cancel(self):
        super(AccountPayment, self).cancel()
        self.write({"invoice_ids": [(5, False, False)]})

    @api.multi
    def set_null(self):
        self.state = "null"


class PaymentInvoiceLine(models.Model):
    _name = "payment.invoice.line"
    _order = "amount desc"

    @api.one
    @api.depends("move_line_id","amount")
    def _line_compute(self):
        if self:
            if self._context.get(u"no_line_compute", False):
                pass
            else:
                self.inv_amount = abs(self.move_line_id.balance)
                # sustract retention from balance
                isr_retention = 0
                if self.move_line_id.invoice_id.journal_id.purchase_type == "informal":
                    tax_retention = self.move_line_id.invoice_id.tax_line_ids.filtered(
                        lambda r: r.tax_id.purchase_tax_type in ("isr", "ritbis"))
                    isr_retention = sum([tax.amount for tax in tax_retention])

                # Inv recidual
                self.balance = abs(self.move_line_id.amount_residual) - abs(isr_retention)
                # amount in inv currency
                self.amount_currency = abs(self.move_line_id.amount_currency)

                if self.amount_currency and self.balance:
                    self.invoice_rate = abs(self.inv_amount / self.amount_currency)
                    if self.invoice_rate:
                        self.amount_currency_pay = abs(self.computed_payemnt() / self.invoice_rate)

    payment_id = fields.Many2one("account.payment")
    move_line_id = fields.Many2one("account.move.line", string="Factura", readonly=True,
                                   domain=[('partner_id', '!=', False)])
    account_id = fields.Many2one(string="Cuenta", related="move_line_id.account_id", readonly=True)
    currency_id = fields.Many2one(string='Currency', related="move_line_id.currency_id",
                                  help="The optional other currency if it is a multi-currency entry.", readonly=True)
    company_currency_id = fields.Many2one(related='move_line_id.company_currency_id', readonly=True,
                                          help='Utility field to express amount currency')
    move_date = fields.Date("Date", related="move_line_id.date", readonly=True)
    date_maturity = fields.Date("Due date", related="move_line_id.date_maturity", readonly=True)

    inv_amount = fields.Monetary("Amount", compute="_line_compute", currency_field='company_currency_id', store=True,
                                 readony=True)
    balance = fields.Monetary("Balance", compute="_line_compute", currency_field='company_currency_id', store=True,
                              readony=True)
    amount_currency = fields.Monetary("Divisa", compute="_line_compute", currency_field='currency_id', store=True,
                                      readony=True)
    invoice_rate = fields.Float("Tasa", compute="_line_compute", digits=(12, 6), store=True, readony=True)
    amount_currency_pay = fields.Float("Divisa", compute="_line_compute", digits=(12, 6), store=True, readony=True)

    amount = fields.Monetary("To pay", default=0.0, currency_field='company_currency_id')
    state = fields.Selection([('draft', 'Draft'), ('request', 'Solicitud'), ('posted', 'Posted'), ('sent', 'Sent'),
                              ('reconciled', 'Reconciled')], related="payment_id.state", readonly=True)
    payment_compute_auto = fields.Boolean(default=False)

    @api.onchange('amount')
    def onchange_amount(self):
        self.payment_compute_auto = False
        if self.amount > self.balance or self.amount < 0:
            self.amount = 0

    def computed_payemnt(self):
        try:
            amount_untaxed = 0
            amount_tax = 0
            for line in self.move_line_id.move_id.line_ids:
                if line.product_id:
                    if line.amount_currency <> 0:
                        amount_untaxed += abs(line.amount_currency)
                    else:
                        amount_untaxed += abs(line.debit + line.credit)

                if line.tax_line_id:
                    if line.amount_currency <> 0:
                        amount_tax += abs(line.amount_currency)
                    else:
                        amount_tax += abs(line.credit + line.debit)

            if self.payment_id.invoice_payemnt_discount:
                discounts = self.payment_id.invoice_payemnt_discount.split(",")

                for discount in discounts:
                    desc = float(discount) / 100
                    amount_dicount = amount_untaxed * desc
                    amount_untaxed -= amount_dicount

            if line.amount_currency <> 0:
                return (amount_untaxed + amount_tax) * self.invoice_rate
            else:
                return amount_untaxed + amount_tax

        except Exception as error:
            _logger.error(error)
            raise exceptions.ValidationError(u"El descuento digitado no es valido")

    @api.one
    def full_pay(self):
        self.amount = self.computed_payemnt()

        if self.amount:
            self.payment_compute_auto = True
        else:
            self.payment_compute_auto = False

    @api.one
    def unfull_pay(self):
        self.amount = 0
        self.payment_compute_auto = False

    @api.multi
    def manual_payment(self):
        res = self.env.ref("advanced_payment.manual_payment_wizard_action").read()[0]
        return res


class PaymentMoveLine(models.Model):
    _name = "payment.move.line"

    payment_id = fields.Many2one("account.payment")
    account_id = fields.Many2one("account.account", string="Account", required=True)
    name = fields.Char("Etiqueta")
    product_id = fields.Many2one('product.product', string='Producto')
    partner_id = fields.Many2one('res.partner', string='Partner', index=True, ondelete='restrict')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    currency_id = fields.Many2one('res.currency', related='payment_id.currency_id', readonly=True,
                                  help='Utility field to express amount currency', store=True)
    company_id = fields.Many2one('res.company', related='account_id.company_id', string='Company', store=True)

    debit = fields.Monetary(string="Debit", default=0.0, currency_field="currency_id")
    credit = fields.Monetary(string="Credit", default=0.0, currency_field="currency_id")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    send_payment_order = fields.Boolean(string='Enviar pago por correo',
                                        help='Marque esta casilla si desea enviar los pago a este cliente o proveedor mientras valida un pago. Esto enviará el email con el informe del pago al cliente / proveedor al momento de validarlo.')
