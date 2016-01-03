# -*- coding: utf-8 -*-

from openerp import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position',
                                         domain=[('supplier','=',False)])
    shop_id = fields.Many2one("shop.ncf.config", string="Sucursal")
    journal_id = fields.Many2one("account.journal", string="Tipo de factura", domain=[('type','=','sale')])
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term', oldname='payment_term')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):
        if self.fiscal_position_id:
            self.env["res.partner"].browse(self.partner_id.id).write({"property_account_position_id": self.fiscal_position_id.id})

    @api.onchange("payment_term_id")
    def onchange_payment_term_id(self):
        if self.payment_term_id:
            self.env["res.partner"].browse(self.partner_id.id).write({"property_payment_term_id": self.payment_term_id.id})

    @api.onchange("shop_id")
    def onchange_sjw(self):
        user_shop_domain = self.env["shop.ncf.config"].get_user_shop_domain()

        user_shops = self.env["shop.ncf.config"].search(user_shop_domain)
        shop_ids = [rec.id for rec in user_shops]

        warehouse_ids = [r.id for r in self.shop_id.warehouse_ids]
        sale_journal_ids = [r.id for r in self.shop_id.sale_journal_ids]

        return {"domain": {"shop_id": [('id','in',shop_ids)],
                           "journal_id": [('id','in',sale_journal_ids)],
                           "warehouse_id": [('id','in',warehouse_ids)]}}

    def update(self, values):
        """ Update record `self[0]` with ``values``. """
        values.update({"payment_term_id": self.partner_id.property_payment_term_id.id,
                       "fiscal_position_id": self.partner_id.property_account_position_id.id})
        super(SaleOrder, self).update(values)






