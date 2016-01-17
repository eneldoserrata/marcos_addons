# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013-2015 Marcos Organizador de Negocios SRL http://marcos.do
#    Write by Eneldo Serrata (eneldo@marcos.do)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields
from openerp.tools.translate import _
from openerp import netsvc, tools
import time

class pos_manager(models.Model):
    _name = "pos.manager"

    name = fields.Char('Name', size=124)
    allow_refund = fields.Boolean("Permitir hacer devoluciones", default=False)
    allow_payments = fields.Boolean('Permitir cobrar', default=True)
    allow_delete_order = fields.Boolean('Permitir eliminar orde no vacías en el POS', default=True)
    allow_discount = fields.Float('Maximo descuento permitido en (%)', default=0)
    allow_edit_price = fields.Boolean('Permitir cambiar el precio', default=True)
    allow_delete_order_line = fields.Boolean('Permitir eliminar línea de la orden', default=True)
    allow_cancel = fields.Boolean("Pueden cancelar ordenes nuevas")
    allow_cash_refund = fields.Boolean("Permitir devolver dinero de la caja", default=False)
    users = fields.Many2many('res.users', 'pos_discount_users', 'discount_id', 'user_id', string='Add Users')


