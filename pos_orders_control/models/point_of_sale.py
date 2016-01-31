# -*- coding: utf-8 -*-
from openerp import models, api
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def wk_order_list(self, name):
        orders_dict = []
        if name:
            orders = self.env['pos.order'].search([('reserve_ncf_seq', 'ilike', name),('state','=','invoiced')], limit=15)

            if not orders:
                orders = self.env['pos.order'].search([('date_order', 'ilike', name),('state','=','invoiced')], limit=15)

            if not orders:
                orders = self.env['pos.order'].search([('partner_id', 'ilike', name),('state','=','invoiced')], limit=15)

            if orders:
                for rec in orders:
                    pos_reference = ""
                    if rec.pos_reference:
                        pos_reference = rec.pos_reference.split(" ")[1]
                    order = {"id": rec.id,
                             "date_order": rec.date_order,
                             "lines": [],
                             "partner_id": rec.partner_id.read(["name"]),
                             "reserve_ncf_seq": rec.reserve_ncf_seq,
                             "statement_ids": [],
                             "credit": rec.credit,
                             "cashier": rec.user_id.id,
                             "uid": pos_reference,
                             "session_id": rec.session_id.id,
                             "origin_ncf": rec.invoice_id.number
                             }
                    for line in rec.lines:
                        product_on_list = False
                        for p in order["lines"]:
                            if p.get("product_id") == line.product_id.id:
                                product_on_list = True
                                p["qty_allow_refund"] += line.qty_allow_refund

                        if not product_on_list:
                            line = {"id": line.id,
                                    "product_id": line.product_id.id,
                                    "note": line.note,
                                    "qty": line.qty,
                                    "price_unit": line.price_unit,
                                    "discount": line.discount,
                                    "tax_ids": [t.id for t in line.tax_ids],
                                    "qty_allow_refund": line.qty_allow_refund}
                            order["lines"].append(line)

                    for pay in rec.statement_ids:
                        if pay.amount > 0:
                            pay = {"id": pay.id,
                                   "statement_id": pay.statement_id.id,
                                   "amount": pay.amount,
                                   "name": pay.journal_id.name}
                            order["statement_ids"].append(pay)

                    orders_dict.append(order)

        return orders_dict
