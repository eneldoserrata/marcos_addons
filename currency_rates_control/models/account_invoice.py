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
from openerp import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @api.depends("currency_id")
    def _get_rate(self):
        self.ensure_one()
        if self.currency_id:
            ResCurrencyRate = self.env['res.currency.rate']
            if self.currency_id.id != self.company_id.currency_id.id:
                currency_rate = ResCurrencyRate.browse(self.currency_id.id)
                if currency_rate:
                    self.rate = currency_rate.rate
            else:
                self.rate = 0

    @api.onchange("date_invoice", "currency_id")
    def onchange_date_invoice(self):
        self._get_rate()

    @api.multi
    def update_currency_wizard(self):
        if not self.date_invoice:
            self.date_invoice = fields.Date.today()

        view_id = self.env.ref(
            "ncf_manager.invoice_currency_change_wizard_form", True)
        return {
            'name': _('Cambiar moneda de la factura'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.currency.change.wizard',
            'view_id': view_id.id,
            'target': 'new',
            'views': False,
            'type': 'ir.actions.act_window',
            'context': {"currency_id": self.currency_id.id}
            }

    @api.multi
    def update_rate_wizard(self):
        view_id = self.env.ref
        ("currency_rates_control.update_rate_wizard_form", True)
        return {
            'name': _('Fecha sin tasa. Actualizar tasa de la moneda'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.rate.wizard',
            'view_id': view_id.id,
            'target': 'new',
            'views': False,
            'type': 'ir.actions.act_window',
            'context': {"default_name": self.date_invoice or fields.Date.today(
                                                                            )}
            }

    rate = fields.Float(u"Tasa del día", compute=_get_rate, digits=(12, 4))
