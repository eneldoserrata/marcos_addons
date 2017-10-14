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

    sync_backend = fields.Boolean('Allow syncing backend')

    user_ids = fields.Many2many('res.users', string='Assigned to')

    # 5/60 = 0.0833 = 5 min - default value
    query_timeout = fields.Float(string='Query timeout', default=0.0833,
                                 help="Waiting period for any message from poll "
                                      "(if we have not received a message at this period, "
                                      "poll will send message ('PING') to check the connection)")

    # 1/60 = 0.01666 = 1 min - default value
    response_timeout = fields.Float(string='Response timeout', default=0.01666,
                                    help="Waiting period for response message (i.e. once message from "
                                         "poll has been sent, it will be waiting for response message ('PONG') "
                                         "at this period and if the message has not been received, the icon turns "
                                         "color to red. Once the connection is restored, the icon changes its color "
                                         "back to green)")

    multi_session_id = fields.Many2one('pos.multi_session', 'Multi-session',
                                       help='Set the same value for POSes where orders should be synced. Keep empty if this POS should not use syncing')
    multi_session_accept_incoming_orders = fields.Boolean('Accept incoming orders', default=True)
    multi_session_replace_empty_order = fields.Boolean('Replace empty order', default=True,
                                                       help='Empty order is deleted whenever new order is come from another POS')
    multi_session_deactivate_empty_order = fields.Boolean('Deactivate empty order', default=False,
                                                          help='POS is switched to new foreign Order, if current order is empty')
    multi_session_message_ID = fields.Integer(default=1, string="Last sent message number")
    multi_session_restart_on_close = fields.Boolean("Reinicia contador multisession")
    allow_lock = fields.Boolean('Allow Screen Lock')
    pos_kitchen_view = fields.Boolean("Kitchen View", default=False)

    @api.multi
    def _send_to_channel(self, channel_name, message):

        notifications = []
        if channel_name == "pos.longpolling":
            channel = self._get_full_channel_name(channel_name)
            notifications.append([channel, "PONG"])
        else:
            for ps in self.env['pos.session'].search([('state', '!=', 'closed'), ('config_id', 'in', self.ids)]):
                channel = ps.config_id._get_full_channel_name(channel_name)
                notifications.append([channel, message])
        if notifications:

            self.env['bus.bus'].sendmany(notifications)
        _logger.debug('POS notifications for %s: %s', self.ids, notifications)
        return 1

    @api.multi
    def _get_full_channel_name(self, channel_name):
        self.ensure_one()
        return '["%s","%s","%s"]' % (self._cr.dbname, channel_name, self.id)

    @api.multi
    def _check_same_floors(self):
        # Проверяем чтобы у всех ПОС у которых одинаковые мультисесии был одинаковый набор этажей (floors).
        # Ранее было решено добавить такое ограничение.
        # TODO
        # У тебя здесь N*(N-1) операций.
        # Можно проще делать:
        # Сделать search в pos.config с аттрибутом groupby='multi_session_id'
        # Потом в каждой группе взять один элемент и сравнить его с каждым. Если хоть одна разница есть, то return False.
        # Тогда будет N + N операций
        for rec in self:
            pos_configs = self.env['pos.config'].search([
                ('multi_session_id', '=', rec.multi_session_id.id),
                ('id', '!=', rec.id)
            ])
            for pos_config_obj in pos_configs:
                a = set(pos_config_obj.floor_ids.ids)
                b = set(rec.floor_ids.ids)
                diff = a.difference(b)
                if diff:
                    return False
        return True

    _constraints = [
        (_check_same_floors, "Points of sale with same multi session must have same floors",
         ['multi_session_id', 'floor_ids']),
    ]


class RestaurantFloor(models.Model):
    _inherit = 'restaurant.floor'

    pos_config_ids = fields.Many2many('restaurant.floor', 'pos_config_floor_rel', 'floor_id', 'pos_config_id',
                                      string="POS configs")


class QtyPosFraction(models.Model):
    _name = "qty.pos.fraction"
    _order = "sequence"

    sequence = fields.Integer()
    name = fields.Char("Nombre")
    qty = fields.Float(u"Fracción", digits=(12,4))