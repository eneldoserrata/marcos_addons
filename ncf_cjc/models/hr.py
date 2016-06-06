# -*- coding: utf-8 -*-

from openerp import fields, models, api, exceptions


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    cjc_journal_ids = fields.Many2many("account.journal", string="Diarios permitidos en caja chica", domain=[('petty_cash','=',True)])
    multi_petty_cash = fields.Integer("Numero de caja chica permitidas", default=1)













