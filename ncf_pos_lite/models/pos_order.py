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

import logging
import time
from datetime import datetime

from odoo import models, fields, api, tools, exceptions, _
from odoo.tools import float_is_zero, DEFAULT_SERVER_DATE_FORMAT

from odoo.tools.safe_eval import safe_eval

import psycopg2
import os
import errno
from functools import wraps

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _payment_fields(self, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(ui_paymentline)
        if ui_paymentline.get("payment_reference", False):
            res.update({"payment_name": "{}".format(ui_paymentline.get("payment_reference"), "")})
        return res

    @api.depends('statement_ids', 'lines.price_subtotal_incl', 'lines.discount')
    def _compute_amount_all(self):
        for order in self:
            refund_payments = 0
            refund_payments += sum(payment.credit for payment in order.refund_payments)
            order.amount_paid = order.amount_return = order.amount_tax = 0.0
            currency = order.pricelist_id.currency_id
            order.amount_paid = sum(payment.amount for payment in order.statement_ids) + refund_payments
            order.amount_return = sum(payment.amount < 0 and payment.amount or 0 for payment in order.statement_ids)
            order.amount_tax = currency.round(
                sum(self._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
            amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
            order.amount_total = order.amount_tax + amount_untaxed

    invoice_number = fields.Char(related="invoice_id.number")
    is_service_order = fields.Boolean("Ordenes que no generan picking")

    is_return_order = fields.Boolean(string='Devolver orden', copy=False)
    return_order_id = fields.Many2one('pos.order', u'Orden de devolución de', readonly=True, copy=False)
    return_status = fields.Selection(
        [('-', 'Sin Devoluciones'), ('Fully-Returned', 'Totalmente devuelto'),
         ('Partially-Returned', 'Devuelto parcialmente'),
         ('Non-Returnable', 'No retornable')], default='-', copy=False, string=u'Estado de devolución')
    refund_payments = fields.Many2many("account.move.line")
    move_name = fields.Char(size=19)
    fiscal_nif = fields.Char()
    order_priority = fields.Integer(default=0)

    def reconcile_befores_session_close(self):
        moves = self.env['account.move']
        for rec in self:
            for st_line in rec.statement_ids:
                if st_line.account_id and not st_line.journal_entry_ids.ids:
                    st_line.sudo().fast_counterpart_creation()
                elif not st_line.journal_entry_ids.ids:
                    _logger.error('Debe revisar las formas de pago de la order {}'.format(rec.name))
                moves = (moves | st_line.journal_entry_ids)
                moves.sudo().post()
        self.sudo()._reconcile_payments()

    def _reconcile_payments(self):
        for order in self:
            aml = order.statement_ids.mapped('journal_entry_ids').mapped(
                'line_ids') | order.account_move.line_ids | order.invoice_id.move_id.line_ids

            aml = aml.filtered(lambda
                                   r: not r.reconciled and r.account_id.internal_type == 'receivable' and r.partner_id == order.partner_id.commercial_partner_id)
            if order.refund_payments:
                aml |= order.refund_payments

            try:
                aml.reconcile()
            except:
                # There might be unexpected situations where the automatic reconciliation won't
                # work. We don't want the user to be blocked because of this, since the automatic
                # reconciliation is introduced for convenience, not for mandatory accounting
                # reasons.
                _logger.error('Reconciliation did not work for order %s', order.name)
                continue

    @api.model
    def create_from_ui(self, orders):
        for order in orders:
            order.update({"to_invoice": True})

        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search([('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]
        order_ids = []

        for tmp_order in orders_to_save:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
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

        order_objs = self.env['pos.order'].browse(order_ids)

        result = {}
        order_list = []
        order_line_list = []
        statement_list = []
        for order_obj in order_objs:
            order_obj.reconcile_befores_session_close()

            vals = {}
            vals['lines'] = []
            if hasattr(order_objs[0], 'return_status'):
                if not order_obj.is_return_order:
                    vals['return_status'] = order_obj.return_status
                    vals['existing'] = False
                    vals['id'] = order_obj.id
                else:
                    order_obj.return_order_id.return_status = order_obj.return_status
                    vals['existing'] = True
                    vals['id'] = order_obj.id
                    vals['return_order_id'] = order_obj.return_order_id.id
                    vals['return_status'] = order_obj.return_order_id.return_status
                    for line in order_obj.lines:
                        line_vals = {}
                        line_vals['id'] = line.original_line_id.id
                        line_vals['line_qty_returned'] = line.original_line_id.line_qty_returned
                        line_vals['existing'] = True
                        order_line_list.append(line_vals)
            vals['statement_ids'] = order_obj.statement_ids.ids
            vals['name'] = order_obj.name
            vals['amount_total'] = order_obj.amount_total
            vals['pos_reference'] = order_obj.pos_reference
            vals['date_order'] = order_obj.date_order
            if order_obj.invoice_id:
                vals['invoice_id'] = order_obj.invoice_id.id
            else:
                vals['invoice_id'] = False
            if order_obj.partner_id:
                vals['partner_id'] = [order_obj.partner_id.id, order_obj.partner_id.name]
            else:
                vals['partner_id'] = False
            if (not hasattr(order_objs[0], 'return_status') or (
                        hasattr(order_objs[0], 'return_status') and not order_obj.is_return_order)):
                vals['id'] = order_obj.id
                for line in order_obj.lines:
                    vals['lines'].append(line.id)
                    line_vals = {}
                    # LINE DATAA
                    line_vals['create_date'] = line.create_date
                    line_vals['discount'] = line.discount
                    line_vals['display_name'] = line.display_name
                    line_vals['id'] = line.id
                    line_vals['order_id'] = [line.order_id.id, line.order_id.name]
                    line_vals['price_subtotal'] = line.price_subtotal
                    line_vals['price_subtotal_incl'] = line.price_subtotal_incl
                    line_vals['price_unit'] = line.price_unit
                    line_vals['product_id'] = [line.product_id.id, line.product_id.name]
                    line_vals['qty'] = line.qty
                    line_vals['write_date'] = line.write_date
                    if hasattr(line, 'line_qty_returned'):
                        line_vals['line_qty_returned'] = line.line_qty_returned
                    # LINE DATAA
                    order_line_list.append(line_vals)
                for statement_id in order_obj.statement_ids:
                    statement_vals = {}
                    # STATEMENT DATAA
                    statement_vals['amount'] = statement_id.amount
                    statement_vals['id'] = statement_id.id
                    if statement_id.journal_id:
                        currency = statement_id.journal_id.currency_id or statement_id.journal_id.company_id.currency_id
                        statement_vals['journal_id'] = [statement_id.journal_id.id,
                                                        statement_id.journal_id.name + " (" + currency.name + ")"]
                    else:
                        statement_vals['journal_id'] = False
                    statement_list.append(statement_vals)
            order_list.append(vals)
        result['orders'] = order_list
        result['orderlines'] = order_line_list
        result['statements'] = statement_list
        return result

    def _prepare_invoice(self):
        res = super(PosOrder, self)._prepare_invoice()
        if self.is_return_order:
            res.update({"type": "out_refund",
                        "origin_invoice_ids": [(4, self.return_order_id.invoice_id.id, _)]})

        if self.fiscal_nif:
            res.update({"fiscal_nif": self.fiscal_nif})

        res.update({"move_name": self.move_name,
                    "user_id": self.user_id.id,
                    "comment": self.note})

        return res

    def _action_create_invoice_line(self, line=False, invoice_id=False):
        InvoiceLine = self.env['account.invoice.line']
        inv_name = line.product_id.name_get()[0][1]

        if self.is_return_order:
            self.return_order_id.invoice_id.write({"refund_invoice_ids": [(4, invoice_id, _)]})

        inv_line = {
            'invoice_id': invoice_id,
            'product_id': line.product_id.id,
            'quantity': abs(line.qty),
            'account_analytic_id': self._prepare_analytic_account(line),
            'name': inv_name,
        }
        # Oldlin trick
        invoice_line = InvoiceLine.sudo().new(inv_line)
        invoice_line._onchange_product_id()
        invoice_line.invoice_line_tax_ids = invoice_line.invoice_line_tax_ids.filtered(
            lambda t: t.company_id.id == line.order_id.company_id.id).ids
        fiscal_position_id = line.order_id.fiscal_position_id
        if fiscal_position_id:
            invoice_line.invoice_line_tax_ids = fiscal_position_id.map_tax(invoice_line.invoice_line_tax_ids,
                                                                           line.product_id, line.order_id.partner_id)
        invoice_line.invoice_line_tax_ids = invoice_line.invoice_line_tax_ids.ids
        # We convert a new id object back to a dictionary to write to
        # bridge between old and new api
        inv_line = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
        inv_line.update(price_unit=line.price_unit, discount=line.discount)

        if line.order_line_note:
            inv_line.update({"name": "{} | {}".format(inv_name, line.order_line_note)})

        return InvoiceLine.sudo().create(inv_line)

    @api.model
    def get_fiscal_data(self, name):
        res = {"fiscal_type": "none", "fiscal_type_name": u"PRE-CUENTA"}

        order_id = False
        timeout = time.time() + 100 * 6  # 5 minutes from now
        while not order_id:
            time.sleep(1)
            if time.time() > timeout:
                break
            self._cr.commit()
            order_id = self.search([('pos_reference', '=', name)])

        if order_id:
            shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()

            res.update({"id": order_id.id, "rnc": order_id.partner_id.vat,
                        "name": order_id.partner_id.name})

            if order_id.is_return_order:
                res.update({"fiscal_type_name": u"NOTA DE CRÉDITO"})

                reference_ncf = order_id.return_order_id.invoice_id.number

                if not order_id.return_order_id.invoice_id:
                    raise exceptions.ValidationError(
                        u"Favor revisar en la orden del pos si la factura fue generada satisfactoriamente o vuelva a intentarlo un unso segundos")

                reference_ncf_type = reference_ncf[9:11]

                if reference_ncf_type in ("01", "14"):
                    res.update({"fiscal_type": "fiscal_note"})
                elif reference_ncf_type == "02":
                    res.update({"fiscal_type": "final_note"})
                elif reference_ncf_type == "15":
                    res.update({"fiscal_type": "special_note"})
                res.update({"origin": reference_ncf})
                sequence = shop_user_config.nc_sequence_id

            elif order_id.partner_id.sale_fiscal_type == "fiscal":
                res.update({"fiscal_type": "fiscal", "fiscal_type_name": "FACTURA CON VALOR FISCAL", "origin": False})
                sequence = shop_user_config.fiscal_sequence_id
            elif order_id.partner_id.sale_fiscal_type == "final":
                res.update(
                    {"fiscal_type": "final", "fiscal_type_name": "FACTURA PARA CONSUMIDOR FINAL", "origin": False})
                sequence = shop_user_config.final_sequence_id
            elif order_id.partner_id.sale_fiscal_type == "gov":
                res.update({"fiscal_type": "fiscal", "fiscal_type_name": "FACTURA GUBERNAMENTAL", "origin": False})
                sequence = shop_user_config.gov_sequence_id
            elif order_id.partner_id.sale_fiscal_type == "special":
                res.update({"fiscal_type": "special", "fiscal_type_name": "FACTURA PARA REGIMENES ESPECIALES",
                            "origin": False})
                sequence = shop_user_config.special_sequence_id

            order_id.move_name = sequence.with_context(ir_sequence_date=fields.Date.today()).next_by_id()
            res.update({"ncf": order_id.move_name})
            order_id.action_pos_order_invoice()
            order_id.create_picking_job()
            return res
        else:
            return False

    @api.model
    def _order_fields(self, ui_order):
        if ui_order:
            fields_return = super(PosOrder, self)._order_fields(ui_order)
            fields_return.update({
                'is_return_order': ui_order.get('is_return_order') or False,
                'return_order_id': ui_order.get('return_order_id') or False,
                'return_status': ui_order.get('return_status') or False,
                'note': ui_order.get('order_note', ''),
                "user_id": ui_order.get("ms_info", {}).get("created", {}).get("user", {}).get("id", {})
            })
            return fields_return

        return {}

    @api.model
    def _process_order(self, pos_order):
        prec_acc = self.env['decimal.precision'].precision_get('Account')
        pos_session = self.env['pos.session'].browse(pos_order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            pos_order['pos_session_id'] = self._get_valid_session(pos_order).id
        if pos_order.get('is_return_order', False):
            pos_order['amount_paid'] = 0
            for line in pos_order['lines']:
                line_dict = line[2]
                line_dict['qty'] = line_dict['qty'] * -1
                original_line = self.env['pos.order.line'].browse(line_dict.get('original_line_id', False))
                original_line.line_qty_returned += abs(line_dict.get('qty', 0))
            for statement in pos_order['statement_ids']:
                statement_dict = statement[2]
                statement_dict['amount'] = statement_dict['amount'] * -1
            pos_order['amount_tax'] = pos_order['amount_tax'] * -1
            pos_order['amount_return'] = 0
            pos_order['amount_total'] = pos_order['amount_total'] * -1

        order = self.create(self._order_fields(pos_order))
        journal_ids = set()
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
                order.add_payment(self._payment_fields(payments[2]))
            journal_ids.add(payments[2]['journal_id'])

        if pos_session.sequence_number <= pos_order.get('sequence_number', 0):
            pos_session.write({'sequence_number': pos_order['sequence_number'] + 1})
            pos_session.refresh()

        if not float_is_zero(pos_order['amount_return'], prec_acc):
            cash_journal_id = pos_session.cash_journal_id.id
            if not cash_journal_id:
                # Select for change one of the cash journals used in this
                # payment
                cash_journal = self.env['account.journal'].search([
                    ('type', '=', 'cash'),
                    ('id', 'in', list(journal_ids)),
                ], limit=1)
                if not cash_journal:
                    # If none, select for change one of the cash journals of the POS
                    # This is used for example when a customer pays by credit card
                    # an amount higher than total amount of the order and gets cash back
                    cash_journal = [statement.journal_id for statement in pos_session.statement_ids if
                                    statement.journal_id.type == 'cash']
                    if not cash_journal:
                        raise exceptions.UserError(_(
                            u"No se encontró ninguna declaración de efectivo para esta sesión. No se puede registrar el efectivo devuelto."))
                cash_journal_id = cash_journal[0].id
            order.add_payment({
                'amount': -pos_order['amount_return'],
                'payment_date': fields.Datetime.now(),
                'payment_name': _('return'),
                'journal': cash_journal_id,
            })
        return order

    def add_payment(self, data):
        statement_id = data.get("statement_id", False)
        if statement_id != 1000000:
            return super(PosOrder, self).add_payment(data)
        else:
            payment_name = data.get("payment_name", False)
            if payment_name:
                out_refund_invoice = self.env["account.invoice"].sudo().search([('number', '=', payment_name)])
                if out_refund_invoice:
                    move_line_ids = out_refund_invoice.move_id.line_ids
                    move_line_ids = move_line_ids.filtered(lambda
                                                               r: not r.reconciled and r.account_id.internal_type == 'receivable' and r.partner_id == self.partner_id.commercial_partner_id)
                    for move_line_id in move_line_ids:
                        self.write({"refund_payments": [(4, move_line_id.id, _)]})

    @api.multi
    def action_pos_order_invoice(self):
        ctx = dict(self._context)
        ctx.update({"mail_auto_subscribe_no_notify": True})
        for rec in self:
            if not rec.partner_id:
                rec.partner_id = rec.config_id.default_partner_id.id

            if not rec.invoice_id:
                super(PosOrder, rec.with_context(ctx)).action_pos_order_invoice()
                rec.invoice_id.sudo().with_context(ctx).action_invoice_open()
                rec.account_move = rec.invoice_id.move_id
                self._reconcile_payments()

    @api.multi
    def create_picking_job(self):
        self.create_picking()

    @api.multi
    def action_pos_order_paid(self):

        if not self.test_paid() and not self.is_return_order:
            raise exceptions.UserError(_("Order is not paid."))
        self.write({'state': 'paid'})

    def test_paid(self):
        """A Point of Sale is paid when the sum
        @return: True
        """

        for order in self:
            if order.return_order_id:
                return True

            if order.lines and not order.amount_total:
                continue

            if not order.lines or abs(order.amount_total) - order.amount_paid > 0.00001:
                return False
        return True

    @api.multi
    def create_picking(self):
        """Create a picking for each order and validate it."""
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        for order in self:
            if not order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                continue
            address = order.partner_id.address_get(['delivery']) or {}
            picking_type = order.picking_type_id
            return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
            order_picking = Picking
            return_picking = Picking
            moves = Move
            location_id = order.location_id.id
            if order.partner_id:
                destination_id = order.partner_id.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id

            if picking_type:
                message = _(
                    "This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (
                              order.id, order.name)
                picking_vals = {
                    'origin': order.name,
                    'partner_id': address.get('delivery', False),
                    'date_done': order.date_order,
                    'picking_type_id': picking_type.id,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                }
                pos_qty = any([x.qty > 0 for x in order.lines])
                if pos_qty:
                    order_picking = Picking.create(picking_vals.copy())
                    # order_picking.message_post(body=message)
                neg_qty = any([x.qty < 0 for x in order.lines])
                if neg_qty:
                    return_vals = picking_vals.copy()
                    return_vals.update({
                        'location_id': destination_id,
                        'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        'picking_type_id': return_pick_type.id
                    })
                    return_picking = Picking.create(return_vals)
                    # return_picking.message_post(body=message)

            for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                if not abs(line.qty) == 0 or not line.type == "service":
                    moves |= Move.create({
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                        'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': abs(line.qty),
                        'state': 'draft',
                        'location_id': location_id if line.qty >= 0 else destination_id,
                        'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                    })

            # prefer associating the regular order picking, not the return
            order.write({'picking_id': order_picking.id or return_picking.id})

            if return_picking:
                order._force_picking_done(return_picking)
            if order_picking:
                order._force_picking_done(order_picking)

            # when the pos.config has no picking_type_id set only the moves will be created
            if moves and not return_picking and not order_picking:
                tracked_moves = moves.filtered(lambda move: move.product_id.tracking != 'none')
                untracked_moves = moves - tracked_moves
                tracked_moves.action_confirm()
                untracked_moves.action_assign()
                moves.filtered(lambda m: m.state in ['confirmed', 'waiting']).force_assign()
                moves.filtered(lambda m: m.product_id.tracking == 'none').action_done()

        return True

    @api.model
    def order_search_from_ui(self, input_txt):
        invoice_ids = self.env["account.invoice"].search([('number', 'ilike', "%{}%".format(input_txt))], limit=100)
        order_ids = self.search([('invoice_id', 'in', invoice_ids.ids)])

        order_list = []
        order_lines_list = []
        for order in order_ids:
            order_json = {
                "amount_total": order.amount_total,
                "date_order": order.date_order,
                "id": order.id,
                "invoice_id": [order.invoice_id.id, order.invoice_id.number],
                "is_return_order": order.is_return_order,
                "name": order.name,
                "pos_reference": order.pos_reference,
                "return_order_id": order.return_order_id.id,
                "return_status": order.return_status,
                "partner_id": [order.partner_id.id, order.partner_id.name],
                "lines": [line.id for line in order.lines],
                "statement_ids": [statement_id.id for statement_id in order.statement_ids],
            }
            order_list.append(order_json)
            for line in order.lines:
                order_lines_json = {
                    "discount": line.discount,
                    "id": line.id,
                    "line_qty_returned": line.line_qty_returned,
                    "price_subtotal": line.price_subtotal,
                    "price_subtotal_incl": line.price_subtotal_incl,
                    "qty": line.qty,
                    "price_unit": line.price_unit,
                    "order_id": [order.id, order.name],
                    "product_id": [line.product_id.id, line.product_id.name],
                }
                order_lines_list.append(order_lines_json)
        return {"wk_order": order_list, "wk_order_lines": order_lines_list}

    @api.model
    def mail_invoice_from_pos(self, pos_order_id, email):

        invoice_id = self.get_invoice_id_from_pos_order_id(pos_order_id)
        template_id = self.env.ref("account.email_template_edi_invoice")
        mail_id = template_id.send_mail(int(invoice_id), True, email_values={"email_to": email, "partner_ids": []})
        return True

    @api.model
    def get_invoice_id_from_pos_order_id(self, pos_order_id):
        pos_order = self.browse(int(pos_order_id))
        if pos_order.invoice_id:
            return pos_order.invoice_id.id
        else:
            return False

    @api.model
    def get_email_from_pos(self, partner_id):
        partner = self.env["res.partner"].browse(int(partner_id))
        if partner.email:
            return partner.email
        else:
            return ""

    @api.model
    def get_credit_by_ncf(self, credit_note_ncf):
        invoice_refund = self.env["account.invoice"].sudo().search([('number', '=', credit_note_ncf)])
        residual_amount = 0

        if not invoice_refund:
            return False

        if invoice_refund:
            residual_amount = invoice_refund.residual

        if invoice_refund == 0:
            return False
        else:
            return {"residual_amount": abs(residual_amount), "partner_id": invoice_refund.partner_id.id}

        @api.multi
        def fix_payment_mistake(self):
            return self.env.ref("fix_payment_mistake_wizard_action")

    @api.model
    def create_sale_order(self, ui_order, cashier):
        vals = {'partner_id': ui_order['partner_id'] or False,
                'user_id': cashier,
                'client_order_ref': 'Point of sale',
                }
        order_id = self.env['sale.order'].create(vals)
        for ui_order_line in ui_order['lines']:
            product = self.env['product.product'].browse(int(ui_order_line[2]['product_id']))
            values = {
                'order_id': order_id.id,
                'product_id': ui_order_line[2]['product_id'],
                'product_uom_qty': ui_order_line[2]['qty'],
                'price_unit': ui_order_line[2]['price_unit'],
                'name': product.name,
                'product_uom': product.uom_id.id,
                'discount': ui_order_line[2]['discount'],
            }
            if product.description_sale:
                values['name'] += '\n' + product.description_sale
            order_line = self.env['sale.order.line'].sudo().create(values)
            order_line._compute_tax_id()
        return {'name': order_id.name, 'id': order_id.id}

    @api.model
    def wk_print_quotation_report(self):
        report_ids = self.env['ir.actions.report.xml'].sudo().search(
            [('model', '=', 'sale.order'), ('report_name', '=', 'sale.report_saleorder')])
        return report_ids and report_ids[0].id or False

    @api.model
    def send_email(self, quotation_id):
        if quotation_id:
            res_id = int(quotation_id)
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data.get_object_reference('sale', 'email_template_edi_sale')[1]
            if template_id:
                template_obj = self.env['mail.template'].browse(template_id)
                mail_confirmed = template_obj.send_mail(res_id, True)

    @api.model
    def get_customer_credit(self, orderdata):
        partner_id = self.env["res.partner"].browse(orderdata["partner_id"])
        amount_total = round(orderdata["amount_total"], 2)

        res = {"nocredit_limit": False}
        if partner_id.credit_limit == 0:
            res.update({"nocredit_limit": True})
            return res

        res = self.get_credit_data(partner_id, amount_total)

        if res["overdue"] or res["credit_exceeded"]:
            if res["overdue"]:
                header = "Pagos pendientes"

            if res["credit_exceeded"]:
                header = u"Este cliente excede el límite de crédito"

            html = u"""
            <div class="tg-wrap"><table class="tg">
              <tr>
                <th class="tg-ds4c" colspan="4">{}</th>
              </tr>
              <tr>
                <td class="tg-yw4l">Limite de crédito:</td>
                <td class="tg-yw4l">{}</td>
                <td class="tg-yw4l">Monto adeudado:</td>
                <td class="tg-yw4l">{}</td>
              </tr>
              <tr>
                <td class="tg-6uc3">Fecha</td>
                <td class="tg-6uc3" colspan="2">Número</td>
                <td class="tg-6uc3">Monto</td>
              </tr>
            
            """.format(header, res["credit_limit"], res["credit"])

            for line in partner_id.unreconciled_aml_ids:
                html += u"""
                  <tr>
                    <td class="tg-yw4l">{}</td>
                    <td class="tg-yw4l" colspan="2">{}</td>
                    <td class="tg-yw4l">{}</td>
                  </tr>
                """.format(line.date, line.move_id.name, line.amount_residual)

            html += u"</table></div>"

            res.update({"raw": html})
            return res

        return res

    def get_credit_data(self, partner_id, amount_total):
        pricelist_id = partner_id.property_product_pricelist
        total_credit = (amount_total / pricelist_id.currency_id.rate) + partner_id.credit
        overdue = False
        for line in partner_id.unreconciled_aml_ids:
            date_maturity = datetime.strptime(line.date_maturity, DEFAULT_SERVER_DATE_FORMAT)
            today = datetime.strptime(fields.Date.today(), DEFAULT_SERVER_DATE_FORMAT)
            if date_maturity < today:
                overdue = True
                break

        return {"credit_exceeded": partner_id.credit_limit < total_credit,
                "total_credit": total_credit,
                "credit_limit": partner_id.credit_limit,
                "credit": partner_id.credit,
                "overdue": overdue,
                "nocredit_limit": False}

    @api.model
    def create_credit_invoice(self, ui_order, cashier):
        order = self.create_sale_order(ui_order, cashier)
        order_id = self.env["sale.order"].browse(order["id"])
        order_id.note = "ORDERN DE COMPRA CLIENTE: {}".format(ui_order["nota"])
        order_id.action_confirm()

        ctx = dict(self._context)
        ctx.update({"open_invoices": True, "active_ids": order_id.ids,"mail_auto_subscribe_no_notify": True})

        sale_order_wizard = self.env["sale.advance.payment.inv"].create({"action_invoice_create": "all"})
        sale_order_wizard.sudo().with_context(ctx).create_invoices()
        invoice_ids = order_id.invoice_ids

        for invoice_id in invoice_ids:
            if invoice_id.state == "draft":
                invoice_id.sudo().with_context(ctx).action_invoice_open()

        self.with_delay(priority=1, channel="root.pos", max_retries=3, eta=20,
                        description="Validando conduce de factura").validate_credit_invoice_piking(invoice_ids, order_id)

        return {"invoice_id": invoice_ids[0].id, "number": invoice_ids[0].number}

    @api.multi
    def validate_credit_invoice_piking(self, invoice_ids, order_id):
        for invoice_id in invoice_ids:
            if invoice_id.partner_id.email:
                template_id = self.env.ref("account.email_template_edi_invoice")
                template_id.send_mail(invoice_id.id, True,
                                      email_values={"email_to": invoice_id.partner_id.email, "partner_ids": []})

        for picking in order_id.picking_ids:
            picking.force_assign()
            picking.do_transfer()


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    line_qty_returned = fields.Integer(u'Línea devuelta', default=0)
    original_line_id = fields.Many2one('pos.order.line', u"Línea original")
    order_line_note = fields.Text('Extra Comments')

    @api.model
    def _order_line_fields(self, line):
        fields_return = super(PosOrderLine, self)._order_line_fields(line)
        fields_return[2].update({'line_qty_returned': line[2].get('line_qty_returned', '')})
        fields_return[2].update({'original_line_id': line[2].get('original_line_id', '')})
        fields_return[2].update({'order_line_note': line[2].get('note', '')})
        return fields_return

    @api.model
    def create(self, vals):
        if vals.get("ms_info", {}).get("created", {}).get("user", {}).get("id", {}):
            uid = vals["ms_info"]["created"]["user"]["id"]
        else:
            uid = 1
        return super(PosOrderLine, self.sudo(uid)).create(vals)
