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
from openerp import models, api, fields
from openerp.exceptions import Warning


class invetory_import(models.TransientModel):
    _name = "invetory.import"

    ref_list = fields.Text("lista de referencia del producto")
    ref_lines = fields.One2many("invetory.import.lines", "inventory_id")

    @api.multi
    def import_product_ref(self):
        cr, uid, context = self.env.cr, self.env.uid, self.env.context
        ref_sum_dict = {}
        if context.get("qty", False) == False:
            ref_list = self.ref_list.split("\n")
        inventory_record = self.env[self._context["active_model"]].browse(self._context["active_id"])
        inventory_record.reset_real_qty()
        invalid_key = []

        if context.get("qty", False) == True:
            for line in self.ref_lines:
                default_code, qty = line.ref_item, line.qty

                if not ref_sum_dict.get(default_code, False):
                    ref_sum_dict[default_code] = qty
                else:
                    ref_sum_dict[default_code] += qty
        else:
            for ref in ref_list:
                if "\t" in ref:
                    default_code, qty = ref.split("\t")
                    qty = float(qty)
                else:
                    default_code, qty = ref, 1.00

                if not ref_sum_dict.get(ref, False):
                    ref_sum_dict[default_code] = qty
                else:
                    ref_sum_dict[default_code] += qty

        for key, value in ref_sum_dict.iteritems():
            key = key.strip()
            if not key == '':
                product_obj = self.env["product.product"].search([('default_code', '=', key)])
                if not product_obj:
                    product_obj = self.env["product.product"].search([('barcode', '=', key)])

                product_in_line = self.env["stock.inventory.line"].search([('product_id','=',product_obj.id),('inventory_id','=',inventory_record.id)])
                if product_obj.exists():
                    if len(product_obj) > 1:
                        duplicate = [prod.name for prod in product_obj]
                        raise Warning(u"Hay varios productos con el mismo codigo de barra - {}".format(duplicate))
                    elif product_obj.standard_price <= 0:
                        raise Warning(u"Debe corregir el costo para este productos - [{}]{}".format(product_obj.default_code ,product_obj.name))

                    if not product_in_line.exists():
                        vals = { 'inventory_id': inventory_record.id,
                                 'location_id': inventory_record.location_id.id,
                                 'package_id': False,
                                 'partner_id': False,
                                 'prod_lot_id': False,
                                 'product_id': product_obj.id,
                                 'product_qty': float(value),
                                 'product_uom_id': product_obj.product_tmpl_id.uom_po_id.id}
                        self.env["stock.inventory.line"].create(vals)
                    else:
                        product_in_line.write({"product_qty": float(value)})
                else:
                    if key not in invalid_key:
                        invalid_key.append(key)

        if invalid_key:
            raise Warning("A introducido una referencia no valida > {}".format(invalid_key))
        else:

            vals = self.env["stock.inventory"]._get_inventory_lines(inventory_record)
            for line in inventory_record.line_ids:
                for key in vals:
                    if key["product_id"] == line.product_id.id:
                        line.theoretical_qty = key["theoretical_qty"]
                        if inventory_record.filter == "invenory_plus":
                            line.product_qty += key["theoretical_qty"]

            return True


class invetory_import(models.TransientModel):
    _name = "invetory.import.lines"

    inventory_id = fields.Many2one("invetory.import")
    ref_item = fields.Char("Referencia", required=True)
    qty = fields.Float("Cantidad", required=True)
