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

from openerp import models, fields, api, exceptions, _, release

import textwrap


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends("rate")
    @api.one
    def _calc_payment_amount(self):
        if self.move_type == "invoice":

            if self.is_base_currency:
                currency_set = set()
                for inv in self.payment_invoice_ids:
                    if inv.amount:
                        currency_set.add(inv.currency_id.id)

                if len(currency_set) > 2:
                    raise exceptions.ValidationError(
                        "El mismo proveedor no puede facturar en mas de dos monedas diferentes.")
                elif len(currency_set) == 2:
                    currency_set.remove(False)
                    self.rate_currency_id = currency_set.pop()
                elif len(currency_set) == 1:
                    self.rate_currency_id = currency_set.pop()
            else:
                self.rate_currency_id = self.company_id.currency_id.id

            # Total a pagar en moneda local
            self.invoice_payment_amount = sum([rec.amount for rec in self.payment_invoice_ids])

            # Total a pagar en moneda extrangera
            self.invoice_payment_amount_currency = sum(
                [rec.amount / rec.invoice_rate for rec in self.payment_invoice_ids if rec.invoice_rate])

            # Total a pagar de la moneda extrangera en moneda local
            invoice_payment_amount_currency_local = sum(
                [rec.amount for rec in self.payment_invoice_ids if rec.currency_id])

            if self.rate_currency_id:
                if self.is_base_currency:
                    self.amount_currency = self.invoice_payment_amount_currency
                    self.payment_amount = self.invoice_payment_amount_currency * self.rate
                    self.floatcurrency_diff = self.currency_diff = invoice_payment_amount_currency_local - self.payment_amount

                else:
                    self.amount_currency = sum([rec.amount for rec in self.payment_invoice_ids if rec.currency_id])
                    if not self.rate:
                        self.rate = 1
                    self.floatcurrency_diff = self.currency_diff = (self.amount_currency - (
                                self.invoice_payment_amount_currency * self.rate)) / self.rate

            if self.currency_diff > 0:
                self.currency_diff_type = "out" if self.payment_type == "inbound" else "in"
            elif self.currency_diff < 0:
                self.currency_diff_type = "in" if self.payment_type == "inbound" else "out"
            elif self.currency_diff == 0:
                self.currency_diff_type = "none"

            if not self.is_base_currency:
                if self.currency_diff_type == "in":
                    self.payment_amount = self.invoice_payment_amount_currency + abs(self.currency_diff)
                elif self.currency_diff_type == "out":
                    self.payment_amount = self.invoice_payment_amount_currency - abs(self.currency_diff)
                else:
                    self.payment_amount = self.invoice_payment_amount_currency

    @api.multi
    def amount_total(self, update_communication=True):
        if self.is_base_currency:
            if self.currency_diff > 0:
                self.amount = self.invoice_payment_amount - abs(self.currency_diff)
            elif self.currency_diff < 0:
                self.amount = self.invoice_payment_amount + abs(self.currency_diff)
            else:
                self.amount = sum([rec.amount for rec in self.payment_invoice_ids])
        else:
            self.amount = self.invoice_payment_amount_currency + (
                        sum([rec.amount for rec in self.payment_invoice_ids if not rec.currency_id]) / self.rate)
            if self.currency_diff > 0:
                self.amount = self.payment_amount + (
                            sum([rec.amount for rec in self.payment_invoice_ids if not rec.currency_id]) / self.rate)
            elif self.currency_diff < 0:
                self.amount = self.payment_amount + (
                            sum([rec.amount for rec in self.payment_invoice_ids if not rec.currency_id]) / self.rate)

        if update_communication:
            full_payment = []
            partinal_payment = []
            for rec in self.payment_invoice_ids:
                if rec.move_line_id:
                    if rec.amount == rec.balance:
                        full_payment.append(rec.move_line_id.invoice_id.number[-4:])
                    elif rec.amount < rec.balance and rec.amount > 0:
                        partinal_payment.append(rec.move_line_id.invoice_id.number[-4:])

            communication = ""

            if full_payment:
                communication += "PAGO FAC: {} ".format(",".join(full_payment))
            if partinal_payment:
                communication += "ABONO FAC: {} ".format(",".join(partinal_payment))

            communication = textwrap.fill(communication, 60)

            self.communication = communication

    @api.depends("currency_id")
    @api.one
    def _check_is_base_currency(self):
        self.is_base_currency = self.currency_id.id == self.company_id.currency_id.id

    move_type = fields.Selection([('auto', 'Automatic'), ('manual', 'Manual'), ('invoice', 'Pay bills')],
                                 string=u"Method of accounting entries",
                                 default="auto", required=True, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('request', 'Solicitud'), ('posted', 'Posted'), ('sent', 'Sent'),
                              ('reconciled', 'Reconciled')], readonly=True, default='draft', copy=False,
                             string="Status")
    payment_move_ids = fields.One2many("payment.move.line", "payment_id", copy=False)
    payment_invoice_ids = fields.One2many("payment.invoice.line", "payment_id", copy=False, limit=1000)
    rate = fields.Float("Tasa", digits=(16, 4))
    currency_diff_type = fields.Selection(
        [('in', 'INGRESO POR DIFERENCIA CAMBIARIA'), ('out', 'GASTO POR DIFERENCIA CAMBIARIA'),
         ("none", "SIN DIFERENCIA CAMBIARIA")], compute="_calc_payment_amount", string="Tipo de diferencia")

    amount_currency = fields.Monetary("Importe divisa", currency_field='rate_currency_id',
                                      compute="_calc_payment_amount")
    rate_currency_id = fields.Many2one("res.currency", string="Divisa de cambio", compute="_calc_payment_amount")
    payment_amount = fields.Monetary("Pago calculado", compute="_calc_payment_amount")
    currency_diff = fields.Monetary("Diferencia cambiaria", compute="_calc_payment_amount")

    invoice_payment_amount = fields.Float(compute="_calc_payment_amount", digit=(16.16))
    invoice_payment_amount_currency = fields.Float(compute="_calc_payment_amount", digit=(16, 16))

    floatcurrency_diff = fields.Float(compute="_calc_payment_amount", digits=(16, 8))

    is_base_currency = fields.Boolean(compute="_check_is_base_currency")

    def _create_payment_entry_manual(self, amount):
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

    @api.model
    def _create_payment_entry_invoice(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        # Remove uneed invoice lines
        [inv.unlink() for inv in self.payment_invoice_ids if inv.amount == 0]

        # add inovices to payment
        self.invoice_ids = self.env["account.invoice"].browse(
            [m_line.move_line_id.invoice_id.id for m_line in self.payment_invoice_ids])

        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)

        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id

        debit, credit, amount_currency, currency_id = aml_obj.with_context(
            date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id,
                                                          invoice_currency)

        move = self.env['account.move'].create(self._get_move_vals())
        debit_invoice_total = 0
        credit_invoice_total = 0

        for inv in self.payment_invoice_ids:
            invoice_id = inv.move_line_id.invoice_id
            # Write line corresponding to invoice payment
            inv_credit = inv.amount if debit > 0 else 0
            inv_debit = inv.amount if credit > 0 else 0

            counterpart_aml_dict = self._get_shared_move_line_vals(inv_debit, inv_credit, amount_currency, move.id,
                                                                   False)
            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(inv.move_line_id.invoice_id))
            counterpart_aml_dict.update({'currency_id': currency_id})

            if inv.currency_id:
                if inv_credit > 0:
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

            debit_invoice_total += counterpart_aml.debit
            credit_invoice_total += counterpart_aml.credit

            retention_amount = 0
            for tax in inv.move_line_id.invoice_id.tax_line_ids:
                if tax.amount < 0:
                    retention_amount += tax.amount
                    aml_obj.create({'account_id': tax.account_id.id,
                                    'amount_currency': False,
                                    'credit': abs(tax.amount),
                                    'currency_id': False,
                                    'debit': 0,
                                    'invoice_id': invoice_id.id,
                                    'journal_id': counterpart_aml_dict.get("journal_id"),
                                    'move_id': counterpart_aml_dict.get("move_id"),
                                    'name': counterpart_aml_dict.get("name", "")+" retencion",
                                    'partner_id': counterpart_aml_dict.get("partner_id"),
                                    'payment_id': counterpart_aml_dict.get("payment_id")})
            if retention_amount:
                aml_obj.create({'account_id': counterpart_aml_dict.get("account_id"),
                                'amount_currency': False,
                                'credit': 0,
                                'currency_id': False,
                                'debit': abs(retention_amount),
                                'invoice_id': invoice_id.id,
                                'journal_id': counterpart_aml_dict.get("journal_id"),
                                'move_id': counterpart_aml_dict.get("move_id"),
                                'name': counterpart_aml_dict.get("name", "") + " retencion",
                                'partner_id': counterpart_aml_dict.get("partner_id"),
                                'payment_id': counterpart_aml_dict.get("payment_id")})

                    # Write counterpart lines
        liquidity_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(amount))

        liquidity_aml_dict.update({"debit": credit_invoice_total,
                                   "credit": debit_invoice_total})
        if self.is_base_currency:
            if self.currency_diff:
                if self.currency_diff > 0:
                    liquidity_aml_dict.update({"amount_currency": False,
                                               "currency_id": False,
                                               "debit": credit_invoice_total - abs(
                                                   self.floatcurrency_diff) if self.payment_type == "inbound" else 0,
                                               "credit": debit_invoice_total - abs(
                                                   self.floatcurrency_diff) if self.payment_type == "outbound" else 0
                                               })
                else:
                    liquidity_aml_dict.update({"amount_currency": False,
                                               "currency_id": False,
                                               "debit": credit_invoice_total + abs(
                                                   self.floatcurrency_diff) if self.payment_type == "inbound" else 0,
                                               "credit": debit_invoice_total + abs(
                                                   self.floatcurrency_diff) if self.payment_type == "outbound" else 0
                                               })
            else:
                liquidity_aml_dict.update({"amount_currency": False,
                                           "currency_id": False,
                                           "debit": credit_invoice_total})


        else:
            if self.currency_diff:
                if self.currency_diff > 0:
                    if self.payment_type == "inbound":
                        amount_currency = self.amount
                    else:
                        amount_currency = self.amount * -1

                    liquidity_aml_dict.update({"amount_currency": amount_currency,
                                               "currency_id": self.currency_id.id,
                                               "debit": credit_invoice_total - abs(
                                                   self.floatcurrency_diff * self.rate) if self.payment_type == "inbound" else 0,
                                               "credit": debit_invoice_total - abs(
                                                   self.currency_diff * self.rate) if self.payment_type == "outbound" else 0})
                else:
                    if self.payment_type == "inbound":
                        amount_currency = self.amount
                    else:
                        amount_currency = self.amount * -1

                    liquidity_aml_dict.update({"amount_currency": amount_currency,
                                               "debit": credit_invoice_total + abs(
                                                   self.floatcurrency_diff * self.rate) if self.payment_type == "inbound" else 0,
                                               "credit": debit_invoice_total + abs(
                                                   self.currency_diff * self.rate) if self.payment_type == "outbound" else 0})
            else:
                liquidity_aml_dict.update({
                                              "amount_currency": self.payment_amount * -1 if self.payment_type == "outbound" else self.payment_amount,
                                              "currency_id": self.currency_id.id})

        if not liquidity_aml_dict.get("account_id", False):
            raise exceptions.ValidationError("De diario de pago no tiene cuenta asignada.")

        aml_obj.create(liquidity_aml_dict)

        if self.currency_diff:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                date=self.payment_date).compute_amount_fields(self.payment_difference, self.currency_id,
                                                              self.company_id.currency_id, invoice_currency)

            writeoff_debit_account_id = self.company_id.currency_exchange_journal_id.default_debit_account_id.id
            writeoff_credit_account_id = self.company_id.currency_exchange_journal_id.default_credit_account_id.id

            if self.is_base_currency:
                if self.payment_type == "inbound":
                    debit_wo = abs(self.floatcurrency_diff) if self.currency_diff > 0 else 0
                    credit_wo = abs(self.currency_diff) if self.currency_diff < 0 else 0
                    amount_currency = self.currency_diff / self.rate
                    writeoff_account_id = writeoff_debit_account_id if self.currency_diff > 0 else writeoff_credit_account_id
                else:
                    debit_wo = abs(self.currency_diff) if self.currency_diff < 0 else 0
                    credit_wo = abs(self.currency_diff) if self.currency_diff > 0 else 0
                    amount_currency = (self.currency_diff / self.rate) * -1
                    writeoff_account_id = writeoff_debit_account_id if self.currency_diff < 0 else writeoff_credit_account_id
            else:
                if self.payment_type == "inbound":
                    debit_wo = abs(self.floatcurrency_diff) * self.rate if self.currency_diff > 0 else 0
                    credit_wo = abs(self.floatcurrency_diff) * self.rate if self.currency_diff < 0 else 0
                    amount_currency = self.currency_diff
                    writeoff_account_id = writeoff_debit_account_id if self.currency_diff > 0 else writeoff_credit_account_id
                else:
                    debit_wo = abs(self.currency_diff) * self.rate if self.currency_diff < 0 else 0
                    credit_wo = abs(self.currency_diff) * self.rate if self.currency_diff > 0 else 0
                    amount_currency = self.currency_diff * -1
                    writeoff_account_id = writeoff_credit_account_id if self.currency_diff > 0 else writeoff_debit_account_id

            writeoff_line['name'] = _('Diferencia cambiaria')
            writeoff_line['account_id'] = writeoff_account_id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency if not self.is_base_currency else False
            writeoff_line['currency_id'] = self.currency_id.id if not self.is_base_currency else False
            writeoff_line['payment_id'] = self.id
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
    def post(self):

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
                rec._create_payment_entry_invoice(amount)
                rec.state = 'posted'

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
                rec.amount_total(update_communication=False)
                [inv_line.unlink() for inv_line in rec.payment_invoice_ids if inv_line.amount == 0]

                if not rec.payment_invoice_ids:
                    raise exceptions.ValidationError("Debe espesificar los montos a pagar por facturas.")

                currency_ids = set()

                for inv in rec.payment_invoice_ids:
                    currency_ids.add(inv.currency_id.id)

                if len(currency_ids) > 1 and not self.rate_currency_id:
                    raise exceptions.ValidationError(
                        "Para pagar una factura registrada en otra moneda debe indicar el tipo de divisa su importe y tasa.")

                rec.state = 'request'
            rec.set_payment_name()

    def reset_move_type(self):
        self.move_type = "auto"

    @api.onchange("payment_invoice_ids")
    def onchange_payment_invoice_ids(self):
        self.amount_total()

    @api.onchange("amount_currency", "rate")
    def onchange_amount_currency_rate(self):
        self.amount_total()

    @api.onchange("currency_id")
    def onchange_currency_id(self):

        # if self.is_base_currency:
        #     self.rate_currency_id = False

        if self.move_type == "invoice":
            self.payment_invoice_ids = self.update_invoice()

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

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0 and self.state != "draft":
            raise exceptions.ValidationError(_('The payment amount must be strictly positive.'))

    @api.onchange("move_type")
    def onchange_move_type(self):
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
        # elif self.move_type == "invoice":
        #     self.payment_invoice_ids = self.update_invoice()

    @api.multi
    def update_invoice(self):
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

            to_reconciled_move_lines = []

            open_invoice = self.env["account.invoice"].search([('state', '=', 'open'),
                                                               ('pay_to', '=', rec.partner_id.id),
                                                               ('journal_id.type', '=', journal_type),
                                                               ('type', '=', invoice_type)])

            if not open_invoice:
                open_invoice += self.env["account.invoice"].search([('state', '=', 'open'),
                                                                    ('partner_id', '=', rec.partner_id.id),
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

            lines_on_payment = [line.move_line_id.id for line in rec.payment_invoice_ids]

            for row in rows:
                if not row.id in lines_on_payment:
                    to_reconciled_move_lines.append(rec.payment_invoice_ids.create({'move_line_id': row.id}))

            move_ids = [move.id for move in to_reconciled_move_lines]
            to_reconciled_move_lines = rec.payment_invoice_ids.browse(move_ids)
            rec.payment_invoice_ids += to_reconciled_move_lines
            # [inv_line.unlink() for inv_line in rec.payment_invoice_ids if not inv_line.move_line_id or inv_line.balance == 0]
        return rec.payment_invoice_ids

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.reset_move_type()

    @api.multi
    def pay_all(self):
        for rec in self:
            for line in rec.payment_invoice_ids:
                line.full_pay()
        return self.amount_total()

    @api.multi
    def unpay_all(self):
        for rec in self:
            for line in rec.payment_invoice_ids:
                line.unfull_pay()
        return self.amount_total()

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


class PaymentInvoiceLine(models.Model):
    _name = "payment.invoice.line"

    @api.one
    @api.depends("move_line_id")
    def _render_amount_sing(self):
        self.net = abs(self.move_line_id.balance)
        retention = sum([tax.amount for tax in self.move_line_id.invoice_id.tax_line_ids if tax.amount < 0])
        self.balance_cash_basis = abs(self.move_line_id.balance_cash_basis - retention)
        self.balance = abs(self.move_line_id.amount_residual - retention)
        self.amount_currency = abs(self.move_line_id.amount_currency)

    @api.one
    @api.depends("move_line_id")
    def _get_invoice_rate(self):
        if self.amount_currency:
            self.invoice_rate = self.net / self.amount_currency

    payment_id = fields.Many2one("account.payment")
    move_line_id = fields.Many2one("account.move.line", string="Factura", readonly=True)
    account_id = fields.Many2one(string="Cuenta", related="move_line_id.account_id", readonly=True)
    currency_id = fields.Many2one(string='Currency', related="move_line_id.currency_id",
                                  help="The optional other currency if it is a multi-currency entry.", readonly=True)
    company_currency_id = fields.Many2one(related='move_line_id.company_currency_id', readonly=True,
                                          help='Utility field to express amount currency')
    move_date = fields.Date("Date", related="move_line_id.date", readonly=True)
    date_maturity = fields.Date("Due date", related="move_line_id.date_maturity", readonly=True)
    net = fields.Monetary("Amount", compute="_render_amount_sing", currency_field='company_currency_id')
    balance_cash_basis = fields.Monetary("Balance", compute="_render_amount_sing", currency_field='company_currency_id')
    balance = fields.Monetary("Balance", compute="_render_amount_sing", currency_field='company_currency_id')

    amount_currency = fields.Monetary("Divisa", compute="_render_amount_sing", currency_field='currency_id')
    amount = fields.Monetary("To pay", default=0.0, currency_field='company_currency_id')
    state = fields.Selection([('draft', 'Draft'), ('request', 'Solicitud'), ('posted', 'Posted'), ('sent', 'Sent'),
                              ('reconciled', 'Reconciled')], related="payment_id.state", readonly=True)
    invoice_rate = fields.Float("Tasa", compute="_get_invoice_rate", digits=(16, 4))

    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount > self.balance:
            self.amount = 0
        elif self.amount < 0:
            self.amount = 0

    @api.one
    def full_pay(self):
        self.amount = self.balance

    @api.one
    def unfull_pay(self):
        self.amount = 0


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


class PaymentRquestReport(models.AbstractModel):
    _name = 'report.advanced_payment.payment_request_report_doc'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('advanced_payment.payment_request_report_doc')
        payments = self.env["account.payment"].browse(self._ids)
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': payments,
        }
        return report_obj.render('advanced_payment.payment_request_report_doc', docargs)
