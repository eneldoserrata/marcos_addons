# -*- coding: utf-8 -*-

from openerp import models, fields, api


class ShopJournalConfig(models.Model):
    _inherit = "shop.ncf.config"

    warehouse_ids = fields.Many2many("stock.warehouse", string="Almacenes")
