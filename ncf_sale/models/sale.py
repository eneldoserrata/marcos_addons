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

from openerp import models, fields, api, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _default_user_shop(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        return shop_user_config["shop_ids"][0]

    def _default_user_journal(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        return shop_user_config["sale_journal_ids"][0]

    def _default_user_wh(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        if not shop_user_config.get("warehouse_ids", False):
            raise exceptions.UserError(u"Su usuario ningun almacen asignado para continuar comuníquese con su administrador.")
        return shop_user_config["warehouse_ids"][0]

    @api.one
    def _get_total_discount(self):
        total_discount = 0.0
        for line in self.order_line:
            total_discount += line.price_unit * ((line.discount or 0.0) / 100.0)
        self.total_discount = total_discount


    total_discount = fields.Monetary(string='Descuento', currency_field="currency_id", compute=_get_total_discount)
    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position',
                                         domain=[('supplier', '=', False)])
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term', oldname='payment_term')

    shop_id = fields.Many2one("shop.ncf.config", string="Sucursal", default=_default_user_shop)
    journal_id = fields.Many2one("account.journal", string="Tipo de factura", domain=[('type', '=', 'sale')], default=_default_user_journal)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, default=_default_user_wh)

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):
        if self.fiscal_position_id and self.partner_id.property_account_position_id.id != self.fiscal_position_id.id:
            self.env["res.partner"].browse(self.partner_id.id).write({"property_account_position_id": self.fiscal_position_id.id})

    @api.onchange("payment_term_id")
    def onchange_payment_term_id(self):
        if self.payment_term_id and self.partner_id.property_payment_term_id.id != self.payment_term_id.id:
            self.env["res.partner"].browse(self.partner_id.id).write({"property_payment_term_id": self.payment_term_id.id})

    @api.onchange("shop_id")
    def onchange_shop_id(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()

        return {"domain": {
            "shop_id": [('shop_id', 'in', shop_user_config["shop_ids"])],
            "journal_id": [('id', 'in', shop_user_config["sale_journal_ids"])],
            "warehouse_id": [('id', 'in', shop_user_config["warehouse_ids"])]
        }}

    def update(self, values):
        values.update({"payment_term_id": self.partner_id.property_payment_term_id.id,
                       "fiscal_position_id": self.partner_id.property_account_position_id.id})
        super(SaleOrder, self).update(values)

    @api.multi
    @api.onchange('partner_shipping_id')
    def onchange_partner_shipping_id(self):
        pass
