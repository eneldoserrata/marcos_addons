# -*- coding: utf-8 -*-

from openerp import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', oldname='fiscal_position',
                                         domain=[('supplier','=',True)])

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        res = super(AccountInvoice, self).purchase_order_change()
        self._onchange_partner_id()
        self.onchange_fiscal_position_id()
        return res
