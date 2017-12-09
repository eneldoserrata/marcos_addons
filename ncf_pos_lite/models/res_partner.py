# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit = fields.Monetary(u'Límite de crédito', default=0.0,
                                   help="Cantidad máxima a ofrecer como crédito a este cliente")
    currency_id = fields.Many2one(related="company_id.currency_id", string="Moneda")
    confirmed_orders_count = fields.Integer(compute='_count_confirmed_orders',
                                            string="Cantidad de pedidos confirmados:")
    confirmed_orders_total = fields.Monetary(compute='_count_confirmed_orders', default=0.00,
                                             string="Monto de pedidos confirmados:")
    draft_invoices_count = fields.Integer(compute='_count_draft_invoices', string="Cantidad de facturas en borrador:")
    draft_invoices_total = fields.Float(compute='_count_draft_invoices', string="Monto de facturas en borrador:")
    receivable = fields.Monetary(compute='_get_receivable', string="Cuenta por cobrar")

    @api.one
    def _get_receivable(self):
        receivable = 0.0

        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        where_params = [tuple(self.ids)] + where_params
        self.env.cr.execute("""SELECT l.move_id
                                  FROM account_move_line l
                                  LEFT JOIN account_account a ON (l.account_id=a.id)
                          LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                                  WHERE act.type IN ('receivable')
                                  AND l.partner_id IN %S
                                  AND l.reconciled IS FALSE
                                  """ + where_clause + """
                                  """,
                            where_params)
        move_ids = self._cr.fetchall()
        if move_ids:
            self.env.cr.execute("""SELECT SUM(l.credit-l.debit)
                                  FROM account_move_line l
                                  LEFT JOIN account_account a ON (l.account_id=a.id)
                          LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                                  WHERE act.type IN ('other')
                                  AND l.partner_id IN %S
                                  AND l.reconciled IS FALSE
                                  AND l.product_id IS NULL
                                  AND l.tax_line_id IS NOT NULL
                                  AND l.move_id IN  %S
                                  """ + where_clause + """
                                  """,
                                (tuple(self.ids), tuple(move_ids),))
            receivable = self._cr.fetchall()[0][0] if not None else 0
        self.receivable = receivable

    @api.one
    def _count_confirmed_orders(self):
        confirmed_orders = self.env['sale.order'].search(
            [('partner_id', '=', self.id), ('state', 'in', ['sale', 'done']), ('invoice_status', '=', 'to invoice')])
        self.confirmed_orders_count = len(confirmed_orders)
        self.confirmed_orders_total = sum(
            map(lambda x: x.amount_total / x.pricelist_id.currency_id.rate, confirmed_orders))

    @api.one
    def _count_draft_invoices(self):
        draft_invoices = self.env['account.invoice'].search([('partner_id', '=', self.id), ('state', '=', 'draft')])
        self.draft_invoices_count = len(draft_invoices)
        self.draft_invoices_total = sum(map(lambda x: x.amount_total / x.currency_id.rate, draft_invoices))

    @api.multi
    def confirm_override(self):
        order_id = self.env.context.get('order_id')
        if order_id:
            sale_order = self.env['sale.order'].browse([order_id])
            if sale_order:
                return sale_order.action_confirm()

    @api.model
    def create_from_ui(self, partner):
        """ create or modify a partner from the point of sale ui.
            partner contains the partner's fields. """
        # image is a dataurl, get the data after the comma
        if partner.get('image'):
            partner['image'] = partner['image'].split(',')[1]
        partner_id = partner.pop('id', False)

        if partner_id:  # Modifying existing partner
            partner.pop('vat', None)
            partner.pop('name', None)
            self.browse(partner_id).with_context(from_pos=True).write(partner)
        else:
            partner_id = self.create(partner).id
        return partner_id


class account_journal(models.Model):
    _inherit = 'account.journal'

    credit = fields.Boolean(string='POS Credit Journal')
