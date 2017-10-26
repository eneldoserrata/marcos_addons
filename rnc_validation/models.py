# -*- coding: utf-8 -*-

from tools import is_identification, _internet_on, is_ncf
import requests
from odoo import models, api, exceptions

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def is_identification(self, value):
        return is_identification(value)

    def is_ncf(self, value, type):
        return is_ncf(value, type)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(ResPartner, self).name_search(name, args=args, operator=operator, limit=100)
        if not res and name:
            if len(name) in (9, 11):
                partners = self.search([('vat', '=', name)])
            else:
                partners = self.search([('vat', 'ilike', name)])

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
        config_parameter = self.env['ir.config_parameter'].sudo()
        api_marcos = config_parameter.get_param("api_marcos")
        if not api_marcos:
            raise exceptions.MissingError(u"Debe configurar la URL de validacón en línea")

        http_proxy = config_parameter.get_param("http_proxy")
        https_proxy = config_parameter.get_param("https_proxy")

        proxies = {}
        if http_proxy != "False":
            proxies.update({"http": http_proxy})

        if http_proxy != "False":
            proxies.update({"https": https_proxy})

        res = requests.get('{}/rnc/{}'.format(api_marcos, fiscal_id), proxies=proxies)
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
                        data['comercial_name'], data.get('payment_regimen', ""), data['status'], data['category'])
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
                raise exceptions.UserError(u"El número de RNC/Cédula no es valido en la DGII.")
            return super(ResPartner, self).create(vals)

    @api.onchange("vat")
    def onchange_vat(self):
        if self.vat and not self._context.get("install_mode", False):
            if self.env["account.invoice"].search_count([('partner_id', '=', 'self.id')]):
                raise exceptions.UserError(
                    u"No puede cambiar el RNC/Cédula ya que este cliente o proveedor tiene facturas.")
            self.check_vals(self.vat)

    @api.model
    def name_create(self, name):
        if self._context.get("install_mode", False):
            return super(ResPartner, self).name_create(name)
        if self._rec_name:
            if name.isdigit():
                partner = self.search([('vat', '=', name)])
                if partner or not len(name) in [9, 11] or not self.get_rnc(name):
                    return (0, "")
            record = self.create({self._rec_name: name})
            return record.name_get()[0]
        else:
            _logger.warning("Cannot execute name_create, no _rec_name defined on %s", self._name)
            return False
