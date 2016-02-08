# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    picking_id = fields.Many2one("stock.picking", "Conduce")

