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
from odoo import models, api, tools
import psycopg2
import time
import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):
        if self.fiscal_position_id and self.partner_id.property_account_position_id.id != self.fiscal_position_id:
            self.partner_id.write(
                {"property_account_position_id": self.fiscal_position_id.id})

    @api.model
    def create_from_ui(self, orders):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search([('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]
        order_ids = []

        for tmp_order in orders_to_save:
            order = tmp_order['data']
            self._match_payment_to_invoice(order)
            pos_order = self._process_order(order)
            order_ids.append(pos_order.id)

            try:
                pos_order.action_pos_order_paid()
            except psycopg2.OperationalError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            if not pos_order.partner_id:
                pos_order.partner_id = pos_order.session_id.config_id.default_partner_id.id
            pos_order.action_pos_order_invoice()
            pos_order.invoice_id.sale_fiscal_type = pos_order.fiscal_position_id.sale_fiscal_type
            pos_order.invoice_id.sudo().action_invoice_open()
            pos_order.account_move = pos_order.invoice_id.move_id
        return order_ids

    def _reconcile_payments(self):
        """This introduces an auto-reconciliation process upon order closing.
        The process restricts the reconciliation to an order individually, i.e. we don't try to cross-reconcile several orders for a customer."""
        for order in self:
            aml = order.statement_ids.mapped('journal_entry_ids') | order.account_move.line_ids
            aml = aml.filtered(lambda r: not r.reconciled and r.account_id.internal_type == 'receivable' and r.partner_id == order.partner_id)
            try:
                aml.reconcile()
            except:
                # There might be unexpected situations where the automatic reconciliation won't
                # work. We don't want the user to be blocked because of this, since the automatic
                # reconciliation is introduced for convenience, not for mandatory accounting
                # reasons.
                continue

    @api.model
    def get_fiscal_data(self, name):
        res = {}

        order_state = False
        while not order_state == 'invoiced':
            time.sleep(1)
            order_id = self.search([('pos_reference', '=', name)])
            if order_id:
                order_state = order_id.state
            self._cr.commit()

        res.update({"ncf": order_id.invoice_id.number})
        if order_id.invoice_id.fiscal_position_id.sale_fiscal_type == "fiscal":
            res.update({"fiscal_type": "fiscal", "fiscal_type_name": "FACTURA CON VALOR FISCAL"})
        elif order_id.invoice_id.fiscal_position_id.sale_fiscal_type == "final":
            res.update({"fiscal_type": "final", "fiscal_type_name": "FACTURA PARA CONSUMIDOR FINAL"})
        elif order_id.invoice_id.fiscal_position_id.sale_fiscal_type == "gov":
            res.update({"fiscal_type": "gov", "fiscal_type_name": "FACTURA GUBERNAMENTAL"})
        elif order_id.invoice_id.fiscal_position_id.sale_fiscal_type == "special":
            res.update({"fiscal_type": "special", "fiscal_type_name": "FACTURA PARA REGIMENES ESPECIALES"})

        return res
