# -*- coding: utf-8 -*-
from odoo import api, models, fields
import logging
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class product_template(models.Model):
    _inherit = "product.template"

    not_returnable = fields.Boolean('No retornable')


