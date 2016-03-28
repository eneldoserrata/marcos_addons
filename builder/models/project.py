# -*- coding: utf-8 -*-
from openerp import models, fields, api


class Project(models.Model):
    _inherit = "project.project"

    @api.one
    @api.depends("purchase_ids", "sale_ids")
    def _count_sale_and_purchase(self):
        if self.purchase_ids:
            self.purchase_count = len(self.purchase_ids)
        else:
            self.purchase_count = 0

        if self.sale_ids:
            self.sale_count = len(self.sale_ids)
        else:
            self.sale_count = 0

    purchase_ids = fields.One2many("purchase.order", "project_id", string="Compras")
    purchase_count = fields.Integer(compute=_count_sale_and_purchase)

    sale_ids = fields.One2many("sale.order", "project_id", string="Ventas")
    sale_count = fields.Integer(compute=_count_sale_and_purchase)

    fiscal_position_id = fields.Many2one("account.fiscal.position", string=u"Posición fiscal de compras", required=True, default=1,
                                         domain=[('supplier','=',True)])