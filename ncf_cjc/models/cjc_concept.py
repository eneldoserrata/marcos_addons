# -*- coding: utf-8 -*-

from odoo import models, fields


class CjcConcept(models.Model):
    _name = "cjc.concept"

    name = fields.Char(u"Descripción", size=50, required=True)
    product_id = fields.Many2one("product.product", string="Producto", required=True)