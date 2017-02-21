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
from openerp import models, fields, api, tools, SUPERUSER_ID
import psycopg2
import time
import logging
_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_partner_id = fields.Many2one("res.partner",
                                         string="Cliente de Contado")
    fiscal_position_ids = fields.Many2many('account.fiscal.position',
                                           string='Fiscal Positions',
                                           domain=[('supplier', '=', False)])


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_from_ui(self, partner):
        """ create or modify a partner from the point of sale ui.
            partner contains the partner's fields. """
        try:
            name = partner.get("name", False)
            if isinstance(int(name), (int,)):
                partner_exist = self.search([('vat', '=', name)])
                if partner_exist:
                    if partner.get("property_account_position_id", False):
                        partner.pop("property_account_position_id", None)
                    partner.update({"id": partner_exist[0].id,
                                    "name": partner_exist.name})
        except:
            pass

        if partner.get('image', False):
            img = partner['image'].split(',')[1]
            partner['image'] = img

        property_account_position_id = partner.get(
            "property_account_position_id", False)
        if property_account_position_id:
            partner.update({
                "property_account_position_id": int(
                    property_account_position_id)})

        if partner.get('id', False):
            partner_id = partner['id']
            del partner['id']
            self.browse(partner_id).write(partner)
        else:
            partner_id = self.create(partner)
            return partner_id.id

        return partner_id


class PosOrder(models.Model):
    _inherit = ["pos.order"]
    _name = 'pos.order'

    fiscal_position_id = fields.Many2one('account.fiscal.position',
                                         'Fiscal Position',
                                         domain=[('supplier', '=', False)])
    reserve_ncf_seq = fields.Char(size=19, copy=False)

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):
        if self.fiscal_position_id and self.partner_id.property_account_position_id.id != self.fiscal_position_id:
            self.partner_id.write(
                {"property_account_position_id": self.fiscal_position_id.id})

    def create_from_ui(self, cr, uid, orders, context=None):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        existing_order_ids = self.search(cr, uid, [('pos_reference', 'in', submitted_references)], context=context)
        existing_orders = self.read(cr, uid, existing_order_ids, ['pos_reference'], context=context)
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]

        order_ids = []

        for tmp_order in orders_to_save:
            order = tmp_order['data']
            self._match_payment_to_invoice(cr, uid, order, context=context)
            order_id = self._process_order(cr, uid, order, context=context)
            order_ids.append(order_id)

            try:
                self.signal_workflow(cr, uid, [order_id], 'paid')
            except psycopg2.OperationalError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            self.action_invoice(cr, uid, [order_id], context)
            order_obj = self.browse(cr, uid, order_id, context)
            # self.invoice_id.move_name = self.reserve_ncf_seq
            self.pool['account.invoice'].signal_workflow(cr, SUPERUSER_ID, [order_obj.invoice_id.id], 'invoice_open')

        return order_ids

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
        if order_id.invoice_id.fiscal_position_id.client_fiscal_type == "fiscal":
            res.update({"fiscal_type": "fiscal", "fiscal_type_name": "FACTURA CON VALOR FISCAL"})
        elif order_id.invoice_id.fiscal_position_id.client_fiscal_type == "final":
            res.update({"fiscal_type": "final", "fiscal_type_name": "FACTURA PARA CONSUMIDOR FINAL"})
        elif order_id.invoice_id.fiscal_position_id.client_fiscal_type == "gov":
            res.update({"fiscal_type": "fiscal", "fiscal_type_name": "FACTURA GUBERNAMENTAL"})
        elif order_id.invoice_id.fiscal_position_id.client_fiscal_type == "special":
            res.update({"fiscal_type": "special", "fiscal_type_name": "FACTURA PARA REGIMENES ESPECIALES"})

        return res
