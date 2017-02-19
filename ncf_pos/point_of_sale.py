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
from openerp import models, fields, api
import time
import logging
_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    note = fields.Char("Nota")


class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_partner_id = fields.Many2one("res.partner",
                                         string="Cliente de contado")
    print_note = fields.Boolean('Imprimir nota en recibo', default=True)
    fiscal_position_ids = fields.Many2many('account.fiscal.position',
                                           string='Fiscal Positions',
                                           domain=[('supplier', '=', False)])


class PosOrder(models.Model):
    _inherit = ["pos.order", 'mail.thread', 'ir.needaction_mixin']
    _name = 'pos.order'

    partner_id = fields.Many2one('res.partner', 'Customer', select=1,
                                 states={'draft': [('readonly', False)],
                                         'paid': [('readonly', False)]},
                                 domain=[('supplier', '=', False)])
    fiscal_position_id = fields.Many2one('account.fiscal.position',
                                         'Fiscal Position',
                                         domain=[('supplier', '=', False)])
    session_id = fields.Many2one('pos.session', 'Session',
                                 required=True,
                                 select=1,
                                 domain="[('state', '=', 'opened')]",
                                 states={'draft': [('readonly', False)]},
                                 readonly=True)
    reserve_ncf_seq = fields.Char(size=19, copy=False)
    origin = fields.Many2one("pos.order", string="Afecta")
    state = fields.Selection([('draft', 'New'),
                              ('cancel', 'Cancelled'),
                              ('paid', 'Paid'),
                              ('done', 'Posted'),
                              ('invoiced', 'Invoiced'),
                              ],
                             'Status', readonly=True, copy=False,
                             default="draft")
    lines = fields.One2many('pos.order.line', 'order_id', 'Order Lines',
                            states={'draft': [('readonly', False)],
                                    'draft_refund': [('readonly', False)]},
                            readonly=True, copy=True)
    date_order = fields.Datetime('Order Date', readonly=True, select=False,
                                 default=fields.datetime.now())

    @api.onchange("session_id")
    def onchange_session_id(self):
        self.partner_id = self.session_id.config_id.default_partner_id.id
        self.pricelist_id = self.partner_id.property_product_pricelist.id
        self.fiscal_position_id = self.partner_id.property_account_position_id.id

    @api.onchange("partner_id")
    def _onchange_partner_id(self, part=False):
        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist.id
            self.fiscal_position_id = self.partner_id.property_account_position_id.id

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):
        if self.fiscal_position_id and self.partner_id.property_account_position_id.id != self.fiscal_position_id:
            self.partner_id.write(
                {"property_account_position_id": self.fiscal_position_id.id})

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)

        if ui_order.get("origin", False):
            res.update({"origin": ui_order["origin"],
                        "state": ui_order.get("order_type", False)})
        return res

    @api.model
    def create_from_ui(self, orders):
        context = {u'lang': u'es_DO', u'tz': u'America/Santo_Domingo',
                   u'uid': 1, "from_ui": True}

        res = super(PosOrder, self).create_from_ui(orders)

        for order_id in res:
            new_order = self.browse(order_id)
            new_order.set_reserve_ncf_seq()

            # self.env.cr.commit()
            order = self.browse(order_id)
            order.with_context(context).generate_ncf_invoice()
        return res

    @api.model
    def action_paid(self):
        if not self.pos_reference:
            self.set_reserve_ncf_seq()
            self.generate_ncf_invoice()

    @api.model
    def set_reserve_ncf_seq(self):
        if not self.partner_id:
            self.partner_id = self.session_id.config_id.default_partner_id.id

        fiscal_type = self.fiscal_position_id.client_fiscal_type
        sequence = self.sale_journal.sequence_id

        if self.sale_journal.ncf_control:
            if fiscal_type == 'fiscal':
                sequence = self.sale_journal.fiscal_sequence_id
            elif fiscal_type == 'gov':
                sequence = self.sale_journal.gov_sequence_id
            elif fiscal_type == 'special':
                sequence = self.sale_journal.special_sequence_id
            else:
                sequence = self.sale_journal.final_sequence_id

        date_order = self.date_order.split(" ")[0]

        next_ncf = True
        while next_ncf:
            ncf_next = sequence.with_context(
                                    ir_sequence_date=date_order).next_by_id()
            _logger.info(
                u"EL SISTEMA SALTO EL NÚMERO {} DEL DIARIO {} PORQUE YA EXISTE DESDE EL PUNTO DE VENTA".format(ncf_next, self.sale_journal.name))

            if not self.search_count([('reserve_ncf_seq', '=', ncf_next), ('sale_journal', '=', self.sale_journal.id)]):
                next_ncf = False

        self.reserve_ncf_seq = ncf_next

    @api.model
    def generate_ncf_invoice(self):
        self.write({'state': 'paid'})
        self.action_invoice()
        self.invoice_id.move_name = self.reserve_ncf_seq
        self.invoice_id.signal_workflow("invoice_open")

    @api.model
    def get_fiscal_data(self, name):
        if name:
            res = {"origin": False}
            ncf = False

            while not ncf:
                time.sleep(1)
                order = self.search([('pos_reference', '=', name)])
                if order:
                    ncf = order.reserve_ncf_seq
                    res.update({"ncf": ncf, "id": order.id})
                self._cr.commit()

            fiscal_code = ncf[9:11]
            if not order.origin:
                if fiscal_code == "01":
                    res.update(
                        {"fiscal_type": "fiscal",
                         "fiscal_type_name": "FACTURA CON VALOR FISCAL"}
                         )
                elif fiscal_code == "02":
                    res.update(
                        {"fiscal_type": "final",
                         "fiscal_type_name": "FACTURA PARA CONSUMIDOR FINAL"}
                         )
                if fiscal_code == "14":
                    res.update(
                        {"fiscal_type": "fiscal",
                         "fiscal_type_name": "FACTURA GUBERNAMENTAL"}
                         )
                elif fiscal_code == "15":
                    res.update(
                        {"fiscal_type": "special",
                         "fiscal_type_name": "FACTURA REGIMENES ESPECIALES"}
                         )
            else:
                reference_ncf = order.origin.invoice_id.number
                reference_ncf_type = reference_ncf[9:11]
                res.update({"fiscal_type_name": "NOTA DE CREDITO"})
                if reference_ncf_type in ("01", "14"):
                    res.update({"fiscal_type": "fiscal_note"})
                elif reference_ncf_type == "02":
                    res.update({"fiscal_type": "final_note"})
                elif reference_ncf_type == "15":
                    res.update({"fiscal_type": "special_note"})
                res.update({"origin": reference_ncf})
            return res
