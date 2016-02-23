# -*- coding: utf-8 -*-
from openerp import models, fields, api


class Project(models.Model):
    _inherit = "project.project"

    @api.one
    def _count_purchase(self):
        res = {}
        if self.purchase_ids:
            res["self.purchase_count"] = len(self.purchase_ids)
        return False

    purchase_ids = fields.One2many("purchase.order", "project_id", string="Compras")
    purchase_count = fields.Integer(compute=_count_purchase)