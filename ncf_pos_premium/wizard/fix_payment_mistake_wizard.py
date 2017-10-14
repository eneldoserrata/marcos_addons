# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
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


from odoo import models, api, fields, exceptions
from odoo.tools import float_compare


class PaymentMistakeWizard(models.TransientModel):
    _name = "payment.mistake.wizard"

    @api.model
    def default_get(self, fields):
        res = super(PaymentMistakeWizard, self).default_get(fields)
        active_id = self._context.get("active_id")
        order_id = self.env["pos.order"].browse(active_id)

        if order_id.session_id.state == "closed":
            raise exceptions.ValidationError(u"La sesión de esta orden ya esta cerrada.")

        if order_id:
            res.update({"order_id": order_id.id})
        return res

    order_id = fields.Many2one("pos.order", string="Pedido", readonly=True)
    amount_total = fields.Float(related="order_id.amount_total", string="Total")
    line_ids = fields.One2many("paymentmistake.wizard.line", "head_id")

    pin_one = fields.Char("Pin uno", required=True)
    aproval_one = fields.Many2one("res.users", readonly=1, string="Autorizado por")

    pin_two = fields.Char("Pin dos", required=True)
    aproval_two = fields.Many2one("res.users", readonly=1, string="Autorizado por")

    @api.onchange("pin_one", "pin_two")
    def onchange_pin(self):

        if self.pin_one:
            self.aproval_one = False

            aproval_user = self.env["res.users"].search([('pos_security_pin', '=', self.pin_one)])
            if aproval_user:
                self.aproval_one = aproval_user.id
            else:
                self.pin_one = False

        if self.pin_two:
            self.aproval_two = False
            aproval_user = self.env["res.users"].search([('pos_security_pin', '=', self.pin_two)])
            if aproval_user:
                self.aproval_two = aproval_user.id
            else:
                self.pin_two = False
        if self.pin_one and self.pin_two:
            if self.pin_one == self.pin_two:
                raise exceptions.ValidationError("El pin uno y dos deben ser diferentes.")

    @api.multi
    def fix_payment(self):
        lines_total = sum([line.amount for line in self.line_ids])

        if float_compare(lines_total, self.amount_total, precision_digits=2) < 0:
            raise exceptions.ValidationError(u"La suma de los montos debe ser igual al total de la orden.")

        if not self.order_id.invoice_id:
            raise exceptions.ValidationError(u"La orden debe estar facturada para realizar esta operación.")

        if not self.order_id.invoice_id.type == "out_invoice":
            raise exceptions.ValidationError(u"Esta operación no esta permitida en notas de crédito.")

        move_line_ids = self.env["account.move.line"]
        move_ids = self.env["account.move"]
        journal_ids = self.env["account.journal"]

        for statement_id in self.order_id.statement_ids:
            journal_ids |= statement_id.journal_entry_ids.journal_id
            move_ids |= statement_id.journal_entry_ids
            move_line_ids |= statement_id.journal_entry_ids.line_ids

        for refund_payment in self.order_id.refund_payments:
            journal_ids |= refund_payment.move_id.journal_id
            move_line_ids |= refund_payment

        move_line_ids |= self.order_id.invoice_id.move_id.line_ids

        move_line_ids = move_line_ids.filtered(lambda r: r.account_id.internal_type == 'receivable')
        move_line_ids.remove_move_reconcile()

        journal_ids = journal_ids.filtered(lambda r: r.update_posted == False)
        for journal_id in journal_ids:
            journal_id.update_posted = True

        move_ids.button_cancel()
        move_ids.unlink()

        for journal_id in journal_ids:
            journal_id.update_posted = False

        self.order_id.statement_ids.unlink()

        for line in self.line_ids:

            statement_id = self.env["account.bank.statement"].search(
                [('pos_session_id', '=', self.order_id.session_id.id), ('journal_id', '=', line.journal_id.id)])
            if not statement_id:
                raise exceptions.ValidationError(u"El tipo de pago no esta disponible para la sesión")

            data = {'amount': line.amount,
                    'journal': line.journal_id.id,
                    'payment_date': self.order_id.date_order,
                    'payment_name': line.ref,
                    'statement_id': statement_id.id}

            self.order_id.add_payment(data)

        for statement_id in self.order_id.statement_ids:
            statement_id.fast_counterpart_creation()

        self.order_id._reconcile_payments()


class FixPaymentMistakeWizard(models.TransientModel):
    _name = "paymentmistake.wizard.line"

    def _get_journal_domain(self):
        active_id = self._context.get("active_id")
        order_id = self.env["pos.order"].browse(active_id)
        journal_ids = [acj.journal_id.id for acj in order_id.session_id.statement_ids]
        if journal_ids:
            return [('id', '=', journal_ids)]
        else:
            return []

    head_id = fields.Many2one("payment.mistake.wizard")
    journal_id = fields.Many2one("account.journal", string="Forma de pago",
                                 domain=_get_journal_domain, required=True)
    amount = fields.Float("Monto", required=True)
    ref = fields.Char("Referencia")
