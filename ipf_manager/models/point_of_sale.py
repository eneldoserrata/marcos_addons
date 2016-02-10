# -*- coding: utf-8 -*-


from openerp import models, fields, api

import time


class PosConfig(models.Model):
    _inherit = "pos.config"


    iface_fiscal_printer = fields.Many2one("ipf.printer.config", string="Impresora fiscal")




