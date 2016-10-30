# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2015 Marcos Organizador de Negocios SRL http://marcos.do
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

from odoo import osv, fields, models
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class stock_inventory(models.Model):
    _inherit = "stock.inventory"

    def _get_available_filters(self):
        res = super(stock_inventory, self)._get_available_filters()

        mode_to_add = [("invenory_plus", "Importar desde los codigos y sumar al inventario actual"),
                       ("inventory_update", "Importar desde los codigos y actualizar el inventario actual")
                       ]
        res += mode_to_add

        return res


    filter = fields.Selection(_get_available_filters, 'Inventory of', required=True,
                                   help="If you do an entire inventory, you can choose 'All Products' and it will prefill the inventory with the current stock.  If you only do some products  "\
                                      "(e.g. Cycle Counting) you can choose 'Manual Selection of Products' and the system won't propose anything.  You can also let the "\
                                      "system propose for a single product / lot /... "),


    def prepare_inventory(self):
        invetory = self
        if invetory.filter in ["invenory_plus", "inventory_update"]:
            return self.write({'state': 'confirm', 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        else:
            return super(stock_inventory, self).prepare_inventory()



