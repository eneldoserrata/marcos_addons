# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


class ShopNcfConfig(models.Model):
    _inherit = "shop.ncf.config"

    warehouse_ids = fields.Many2many("stock.warehouse", string="Almacenes")

    @api.model
    def get_user_shop_config(self):
        res = super(ShopNcfConfig, self).get_user_shop_config()

        user_shops = self.browse(res["shop_ids"])
        warehouse_ids = list(set(sum([[warehouse_id.id for warehouse_id in rec.warehouse_ids] for rec in user_shops], [])))
        if not warehouse_ids:
            raise exceptions.UserError("Su sucursal no tiene almacenes asignados.")

        res.update({"warehouse_ids": warehouse_ids})
        return res
