# -*- coding: utf-8 -*-

from openerp import models, fields, api
from lxml import etree

class account_analytic_line(models.Model):
    _inherit = 'account.analytic.line'

    categ_id = fields.Many2one(related="product_id.product_tmpl_id.categ_id", store=True)


class AccountMove(models.Model):
    _inherit = "account.move.line"

    categ_id = fields.Many2one(related="product_id.product_tmpl_id.categ_id", store=True)