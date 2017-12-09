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


from odoo import models, fields, api, exceptions, _
from odoo.addons.account.wizard.pos_box import CashBox


class PosBox(CashBox):
    _register = False

    @api.multi
    def run(self):
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', [])

        if active_model == 'pos.session' and self.refund_with_ncf:
            if self.residual == 0:
                raise exceptions.ValidationError(u"La nota de crédito no es válida.")
            elif self.aproval_one == self.aproval_two:
                raise exceptions.ValidationError(u"La aprobación debe ser por usuarios diferentes.")
            elif not self.aproval_one or not self.aproval_two:
                raise exceptions.ValidationError(u"Autorización incompleta.")
            elif self.amount <= 0:
                raise exceptions.ValidationError(u"El monto debe ser mayor que 0.")
            elif self.amount > self.residual:
                raise exceptions.ValidationError(u"El monto no puede ser mayor al balance de la nota de crédito.")

            bank_statements = [session.cash_register_id for session in self.env[active_model].browse(active_ids) if
                               session.cash_register_id]
            if not bank_statements:
                raise exceptions.UserError(_("There is no cash register for this PoS Session"))
            return self._run(bank_statements)

        elif active_model == 'pos.session':
            bank_statements = [session.cash_register_id for session in self.env[active_model].browse(active_ids) if
                               session.cash_register_id]
            if not bank_statements:
                raise exceptions.UserError(_("There is no cash register for this PoS Session"))
            return self._run(bank_statements)
        else:
            return super(PosBox, self).run()

    @api.multi
    def _calculate_values_for_statement_line(self, record):
        res = super(PosBox, self)._calculate_values_for_statement_line(record)
        active_model = self.env.context.get('active_model', False)
        if active_model == 'pos.session' and self.refund_with_ncf:
            res.update({u"name": u"Autorizado por: {}/{} | NCF: {} | {}".format(self.aproval_one.name,
                                                                              self.aproval_two.name,
                                                                              self.invoice_refund_number,
                                                                              self.name)})
        return res

    @api.one
    def _create_bank_statement_line(self, record):

        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', [])
        if active_model == 'pos.session' and self.refund_with_ncf:
            values = self._calculate_values_for_statement_line(record)
            values.update({"statement_id": record.id})
            st_line = self.env["account.bank.statement.line"].create(values)
            st_line.sudo().fast_counterpart_creation()
            moves = self.env['account.move']
            moves_line = self.env['account.move.line']

            moves = (moves | st_line.journal_entry_ids)
            out_refund = self.env["account.invoice"].search([('number','=',self.invoice_refund_number)])


            transfer_account_id = record.journal_id.company_id.transfer_account_id
            aml_transfer = [line for line in moves.line_ids if line.account_id == transfer_account_id][0]
            aml_out_refund = out_refund.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type == 'receivable')
            moves.button_cancel()
            aml_transfer.with_context(check_move_validity=False).write({"account_id": aml_out_refund.account_id.id, "partner_id": aml_out_refund.partner_id.id})
            aml_to_rencile = moves_line | aml_out_refund | aml_transfer
            moves.sudo().post()
            aml_to_rencile.reconcile()

            session = self.env[active_model].browse(active_ids)
            session.message_post(body=u"Entrada de devolución de efectivo {}".format(moves.name))

            return {}
        else:
            res = super(PosBox, self)._create_bank_statement_line(record)

        return res


class PosBoxOut(PosBox):
    _inherit = 'cash.box.out'

    @api.model
    def default_get(self, fields):
        res = super(PosBoxOut, self).default_get(fields)
        active_model = self.env.context.get('active_model', False)
        if self.env.user.can_refund_money and active_model == 'pos.session':
            res.update({"refund_with_ncf": True})
        return res

    invoice_refund_number = fields.Char(u"NCF de la nota de crédito")
    residual = fields.Float("Balance", readonly=1)
    refund_with_ncf = fields.Boolean()

    pin_one = fields.Char("Pin uno")
    aproval_one = fields.Many2one("res.users", readonly=1, string="Autorizado por")

    pin_two = fields.Char("Pin dos")
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

    @api.onchange("invoice_refund_number")
    def onchange_invoice_refund_number(self):
        self.residual = 0
        if self.invoice_refund_number:
            nc = self.env["account.invoice"].search([('number', '=', self.invoice_refund_number)])
            if nc:
                self.residual = nc.residual
