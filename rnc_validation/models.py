# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
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
from tools import is_identification, _internet_on
import requests
from openerp import models, api, exceptions

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(ResPartner, self).name_search(name, args=args, operator=operator, limit=100)
        if not res and name:
            partners = self.search([('vat','ilike',name)])

            if not partners:
                if self._context.get("search_default_customer", False):
                    partners = self.search(['|','&',('phone','ilike',name),('mobile','ilike',name),('customer','=',True)])
                elif self._context.get("search_default_supplier", False):
                    partners = self.search(['|','&',('phone','ilike',name),('mobile','ilike',name),('supplier','=',True)])



            if partners:
                res = partners.name_get()
        return res

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
        if self._context.get("install_mode", False):
            return super(ResPartner, self).check_vals(vals)
        if isinstance(vals, unicode):
            vals = {"vat": vals}
        if vals:
            vat_or_name = vals.get("vat", False) or vals.get("name", False)
            if vat_or_name:
                if vat_or_name.isdigit():
                    fiscal_id = vat_or_name.strip()
                    vals = self.validate_fiscal_id(fiscal_id)
        return vals

    @api.model
    def create(self, vals):
        if self._context.get("install_mode", False):
            return super(ResPartner, self).create(vals)
        elif vals:
            validation = self.check_vals(vals)
            if validation:
                vals.update(validation)
            else:
                raise exceptions.UserError(u"El número de RNC/Cédula no es vEalido en la DGII.")
            return super(ResPartner, self).create(vals)

    @api.onchange("vat")
    def onchange_vat(self):
        if self.vat and not self._context.get("install_mode", False):
            if self.env["account.invoice"].search_count([('partner_id', '=', 'self.id')]):
                raise exceptions.UserError("No puede cambiar el RNC/Cédula ya que este cliente o proveedor tiene facturas.")
            self.check_vals(self.vat)

    @api.model
    def name_create(self, name):
        if self._context.get("install_mode", False):
            return super(ResPartner, self).name_create(name)
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
