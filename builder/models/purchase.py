# -*- coding: utf-8 -*-

from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _get_fiscal_position_domain(self):
        domain = [('supplier','=',True)]
        if self.project_id:
            if self.project_id.fiscal_position_ids:
                fiscal_position_alowed = [rec.id for rec in self.project_id.fiscal_position_ids]
                domain = [('id', 'in', tuple(fiscal_position_alowed))]
        return domain


    project_id = fields.Many2one("project.project", string="Projecto")
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', oldname='fiscal_position',
                                         domain=_get_fiscal_position_domain)

    @api.onchange("project_id")
    def onchange_project_id(self):
        for line in self.order_line:
            line.account_analytic_id = self.project_id.analytic_account_id.id
        return {'domain': {'fiscal_position_id': self._get_fiscal_position_domain()}}

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        return super(PurchaseOrder, self).onchange_partner_id()



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.order_id.project_id.id:
            self.account_analytic_id = self.order_id.project_id.id
        
        return super(PurchaseOrderLine, self).onchange_product_id()

