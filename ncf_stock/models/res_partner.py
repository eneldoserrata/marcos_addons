# -*- coding: utf-8 -*-

from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_method = fields.Selection([
        ('purchase', 'En cantidades pedidas'),
        ('receive', 'En cantidades recibidas'),
        ], string="Control de factura de compra", default="receive")
