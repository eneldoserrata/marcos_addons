# -*- coding: utf-8 -*-

from odoo import models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        without_tax = self.partner_id.credit_limit_without_tax
        net_receivable = ((self.partner_id.credit - self.partner_id.receivable_tax)
                          if (self.partner_id.receivable_tax < self.partner_id.credit) else self.partner_id.credit)
        confirmed_orders_total = 0.00
        draft_invoices_total = 0.00
        confirmed_orders = self.search([('partner_id', '=', self.partner_id.id), ('state', 'in', ['sale', 'done']),
                                        ('invoice_status', '=', 'to invoice')])
        draft_invoices = self.env['account.invoice'].search(
            [('partner_id', '=', self.partner_id.id), ('state', '=', 'draft')])
        if draft_invoices:
            draft_invoices_total = sum(map(
                lambda x: x.amount_untaxed / x.currency_id.rate if without_tax else x.amount_total / x.currency_id.rate,
                draft_invoices))
        if confirmed_orders:
            confirmed_orders_total = sum(map(lambda
                                                 x: x.amount_untaxed / x.pricelist_id.currency_id.rate if without_tax else x.amount_total / x.pricelist_id.currency_id.rate,
                                             confirmed_orders))
        total_credit = ((
                        self.amount_untaxed / self.pricelist_id.currency_id.rate if without_tax else self.amount_total / self.pricelist_id.currency_id.rate) +
                        (
                        net_receivable if without_tax else self.partner_id.credit) + confirmed_orders_total + draft_invoices_total)

        if self.partner_id.credit_limit < total_credit:
            extra = total_credit - self.partner_id.credit_limit
            view = self.env['ir.model.data'].xmlid_to_res_id('customers_credit_limit.climit_override_credit_form')
            ctx = self.env.context.copy()
            ctx.update({'order_id': self.id})
            return {
                'name': _(
                    u'Warning: Credit limit will be exceeded by {}{:,.2f}'.format(self.company_id.currency_id.symbol,
                                                                                  extra)),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'res.partner',
                'views': [(view, 'form')],
                'view_id': view,
                'target': 'new',
                'res_id': self.partner_id.id,
                'context': ctx,
            }
        super(SaleOrder, self).action_confirm()
