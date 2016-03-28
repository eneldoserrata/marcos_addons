# -*- coding: utf-8 -*-

from openerp import models, fields


class Sale(models.Model):
    _inherit = "sale.order"

    project_id = fields.Many2one("project.project", string="Projecto")