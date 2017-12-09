# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    floor_ids = fields.Many2many('restaurant.floor', 'pos_config_floor_rel', 'pos_config_id', 'floor_id',
                                 string="Restaurant Floors", help='The restaurant floors served by this point of sale')

    default_partner_id = fields.Many2one("res.partner", string=u"Cliente de contado", required=False)

    order_loading_options = fields.Selection([("current_session", u"Cargar órdenes de la sesión actual"),
                                              ("n_days", u"Ordenes de carga de los últimos días")],
                                             default='current_session', string=u"Opciones de carga")
    number_of_days = fields.Integer(string=u'Número de días pasados', default=10)

    on_order = fields.Boolean(u'Añadir nota a la orden completa', default=True)
    receipt_order_note = fields.Boolean('Imprimir notas en el recibo', default=True)

    display_person_add_line = fields.Boolean('Display session information',
                                             help="If checked, on pos screen we'll all information of cashier add the line")
    user_ids = fields.Many2many('res.users', string='Assigned to')
    allow_lock = fields.Boolean('Allow Screen Lock')



class RestaurantFloor(models.Model):
    _inherit = 'restaurant.floor'

    pos_config_ids = fields.Many2many('restaurant.floor', 'pos_config_floor_rel', 'floor_id', 'pos_config_id',
                                      string="POS configs")


class QtyPosFraction(models.Model):
    _name = "qty.pos.fraction"
    _order = "sequence"

    sequence = fields.Integer()
    name = fields.Char("Nombre")
    qty = fields.Float(u"Fracción", digits=(12, 4))
