# -*- coding: utf-8 -*-

from openerp import models, fields, api


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.multi
    def write(self, vals):
        res = super(MrpBom, self).write(vals)
        for rec in self:
            bom_cost = 0.0
            for line in rec.bom_line_ids:
                bom_cost += line.product_id.standard_price*line.product_qty
            self.product_tmpl_id.standard_price = bom_cost

        return res