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
from odoo import api, models, fields, SUPERUSER_ID, exceptions


class pos_config(models.Model):
    _inherit = "res.users"

    allow_payments = fields.Boolean(u"Permitir cobrar", default=True)
    allow_delete_order = fields.Boolean(u"Permitir eliminar fin que no esté vacía", default=True)
    allow_discount = fields.Float(u"Maximo descuento permitido en (%)", default=0)
    allow_edit_price = fields.Boolean(u"Permitir cambiar el precio", default=True)
    allow_delete_order = fields.Boolean(u"Permitir eliminar orde no vacías en el POS", default=True)
    allow_refund = fields.Boolean(u"Permitir hacer devoluciones", default=False)
    allow_delete_order_line = fields.Boolean(u"Permitir eliminar línea de la orden", default=True)
    allow_cancel = fields.Boolean(u"Pueden cancelar ordenes nuevas")
    allow_cash_refund = fields.Boolean(u"Permitir devolver dinero de la caja", default=False)
    allow_credit = fields.Boolean(u"Permitir facturar a credito", default=False)
    allow_line_rename = fields.Boolean(u"Permitir cambiar descripcion del producto", default=False)


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange("discount")
    def onchange_dicount(self):
        if self.discount:
            if self._context.get("type", False) in ('out_invoice', 'out_refund'):
                if self.discount > self.env.user.allow_discount:
                    self.discount = 0
                    return {
                        'value': {'discount': 0},
                        'warning': {'title': "Cuidado", 'message': "Usted no tiene permitido aplicar este descuento"},
                    }
            elif self._context.get("type", False) in ('in_invoice', 'in_refund'):
                if self.discount > 100:
                    self.discount = 0
                    return {
                        'value': {'discount': 0},
                        'warning': {'title': "Cuidado", 'message': "El descuento no debe superar el 100%"},
                    }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange("discount")
    def onchange_dicount(self):
        if self.discount:
            if self.discount > self.env.user.allow_discount:
                self.discount = 0
                return {
                    'value': {'discount': 0},
                    'warning': {'title': "Cuidado", 'message': "Usted no tiene permitido aplicar este descuento"}
                }
