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


from odoo import models, fields, api, exceptions


class ManualPaymentWizard(models.TransientModel):
    _name = "manual.payment.wizard"
    
    @api.model
    def default_get(self, fields):
        res = super(ManualPaymentWizard, self).default_get(fields)
        active_id = self._context.get("active_id", False)
        if active_id:
            inv = self.env["payment.invoice.line"].browse(active_id)
            res.update({"currency_id": inv.currency_id.id,
                        "line_id": inv.id,
                        "move_line_id": inv.move_line_id.name_get()[0][1]})
        return res

    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=1)
    amount = fields.Monetary("Importe", currency_field="currency_id")
    line_id = fields.Many2one("payment.invoice.line")
    move_line_id = fields.Char( string="Factura", readonly=True)

    @api.multi
    def apply_manual_payment(self):
        if self.line_id.amount_currency > 0:
            self.line_id.amount = self.amount*self.line_id.invoice_rate
        else:
            self.line_id.amount = self.amount

        self.line_id.payment_compute_auto = False