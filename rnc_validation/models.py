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

from tools import is_identification, _internet_on
import requests
from openerp import models, api, exceptions

import logging

_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit = "res.partner"

    @api.model
    def name_search(self, name, args=None, operator='ilike', context=None, limit=100):
        args = args or []

        recs = self.search([], limit=limit)

        if name:
            recs = self.search([('name', operator, name)] + args, limit=limit)

        if not recs:
            recs = self.search([('vat', operator, name)] + args, limit=limit)
        elif not recs:
            recs = self.search([('phone', operator, name)] + args, limit=limit)
        elif not recs:
            recs = self.search([('mobile', operator, name)] + args, limit=limit)

        return recs.name_get()

    @api.model
    def vat_is_unique(self, fiscal_id):
        partner = self.search([('vat', '=', fiscal_id)])
        if partner:
            raise exceptions.UserError(u"Ya fue registrada una empresa con este numero de RNC/Cédula")
        return False

    def get_rnc(self, fiscal_id):
        res = requests.get('http://api.marcos.do/rnc/%s' % fiscal_id)
        if res.status_code == 200:
            return res.json()
        else:
            return False

    def validate_fiscal_id(self, fiscal_id):
        vals = {}

        if not len(fiscal_id) in [9, 11]:
            raise exceptions.ValidationError(u"Debe colocar un numero de RNC/Cedula valido!")
        else:
            if _internet_on():
                data = self.get_rnc(fiscal_id)
                if data:
                    vals['vat'] = data['rnc'].strip()
                    vals['name'] = data['name'].strip()
                    vals["comment"] = u"Nombre Comercial: {}, regimen de pago: {},  estatus: {}, categoria: {}".format(
                        data['comercial_name'], data['payment_regimen'], data['status'], data['category'])
                    vals.update({"company_type": "company"})
                    if len(fiscal_id) == 9:
                        vals.update({"company_type": "company"})
                    else:
                        vals.update({"company_type": "person"})
        return vals

    @api.model
    def check_vals(self, vals):
        validation = {}

        vat_or_name = vals.get("vat", False) or vals.get("name", False)
        if vat_or_name.isdigit():
            fiscal_id = vat_or_name.strip()
            validation = self.validate_fiscal_id(fiscal_id)

        return validation

    @api.model
    def create(self, vals):
        validation = self.check_vals(vals)
        if validation:
            vals.update(validation)
        return super(res_partner, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("vat", False) or vals.get("name", False):
            for rec in self:
                self.vat_is_unique(vals)
                if vals.get("vat", False):
                    if self.env["account.invoice"].search_count([('partner_id', '=', 'self.id')]):
                        raise exceptions.UserError("No puede cambiar el RNC/Cédula al que le ha creado facturas")
                validation = self.check_vals(vals)
                if validation:
                    vals.update(validation)

        return super(res_partner, self).write(vals)

    @api.model
    def name_create(self, name):
        if self._rec_name:
            if name.isdigit():
                partner = self.search([('vat', '=', name)])
                if partner or not len(name) in [9, 11] or not self.get_rnc(name):
                    return (0,"")
            record = self.create({self._rec_name: name})
            return record.name_get()[0]
        else:
            _logger.warning("Cannot execute name_create, no _rec_name defined on %s", self._name)
            return False
