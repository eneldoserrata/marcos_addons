# -*- coding: utf-8 -*-

from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    project_id = fields.Many2one("project.project", string="Projecto")
    task_id = fields.Many2one("project.task", "Tarea")

    @api.onchange("project_id")
    def onchange_project_id(self):
        for line in self.order_line:
            line.account_analytic_id = self.project_id.analytic_account_id.id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.order_id.project_id.id:
            self.account_analytic_id = self.order_id.project_id.id
        
        return super(PurchaseOrderLine, self).onchange_product_id()