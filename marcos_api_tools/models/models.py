# -*- coding: utf-8 -*-
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

import requests

from odoo import models, api, exceptions, fields
from tools import is_ncf, _internet_on, is_identification

import logging

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf
except(ImportError, IOError) as err:
    _logger.debug(err)


try:
    from stdnum.do import ncf
except(ImportError, IOError) as err:
    _logger.debug(err)


class MarcosApiTools(models.Model):
    _name = 'marcos.api.tools'

    def is_identification(self, value):
        return is_identification(value)

    def is_ncf(self, value, type):
        return is_ncf(value, type)

    @api.model
    def setup(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        http_proxy = config_parameter.get_param("http_proxy")
        if not http_proxy:
            config_parameter.create({"key": "http_proxy", "value": "False"})
        https_proxy = config_parameter.get_param("https_proxy")
        if not https_proxy:
            config_parameter.create({"key": "https_proxy", "value": "False"})
        api_marcos = config_parameter.get_param("api_marcos")
        if not api_marcos:
            config_parameter.create({"key": "api_marcos", "value": "http://api.marcos.do"})

    def get_marcos_api_request_params(self):

        config_parameter = self.env['ir.config_parameter'].sudo()
        http_proxy = config_parameter.get_param("http_proxy")
        https_proxy = config_parameter.get_param("https_proxy")
        api_marcos = config_parameter.get_param("api_marcos")

        if not api_marcos:
            raise exceptions.ValidationError(
                u"Debe configurar la URL de validación en línea: es la variable api_marcos en el menu de parametros del sistema")
        if not _internet_on(api_marcos):
            return exceptions.ValidationError(u"No se pudo validar con la DGII por falta de conexión a internet.")

        proxies = {}
        if http_proxy != "False":
            proxies.update({"http": http_proxy})

        if http_proxy != "False":
            proxies.update({"https": https_proxy})

        return (1, api_marcos, proxies)

    def rnc_cedula_validation(self, fiscal_id):
        invalid_fiscal_id_message = (500, u"RNC/Cédula invalido", u"El número de RNC/C´ula no es valido.")
        if not is_identification(fiscal_id):
            return invalid_fiscal_id_message
        else:
            request_params = self.get_marcos_api_request_params()
            if request_params[0] == 1:
                res = requests.get('{}/rnc/{}'.format(request_params[1], fiscal_id), proxies=request_params[2])
                if res.status_code == 200:
                    dgii_data = res.json()
                    dgii_data["vat"] = dgii_data['rnc']
                    dgii_data[
                        "comment"] = u"Nombre Comercial: {}, regimen de pago: {},  estatus: {}, categoria: {}".format(
                        dgii_data['comercial_name'], dgii_data.get('payment_regimen', ""), dgii_data['status'],
                        dgii_data['category'])
                    if len(fiscal_id) == 9:
                        dgii_data.update({"company_type": u"company"})
                        dgii_data.update({"is_company": u"True"})
                    else:
                        dgii_data.update({"company_type": u"person"})
                    return (1, dgii_data)
                else:
                    return invalid_fiscal_id_message

    def invoice_ncf_validation(self, invoice):
        if not invoice.journal_id.ncf_remote_validation:
            return True

        elif not invoice.journal_id.purchase_type in ['exterior', 'import',
                                                      'others'] and invoice.journal_id.type == "purchase":

            if invoice.id:
                inv_in_draft = self.env["account.invoice"].search_count([('id', '!=', invoice.id),
                                                                         ('partner_id', '=', invoice.partner_id.id),
                                                                         ('move_name', '=', invoice.move_name),
                                                                         ('state', 'in', ('draft', 'cancel'))])
            else:
                inv_in_draft = self.env["account.invoice"].search_count([('partner_id', '=', invoice.partner_id.id),
                                                                         ('move_name', '=', invoice.move_name),
                                                                         ('state', 'in', ('draft', 'cancel'))])

            if inv_in_draft:
                return (200, u"Ncf duplicado", u"El número de comprobante fiscal digitado para este proveedor \n"
                                               u"ya se encuentra en una factura en borrador o cancelada.")

            inv_exist = self.env["account.invoice"].search_count(
                [('partner_id', '=', invoice.partner_id.id), ('number', '=', invoice.move_name),
                 ('state', 'in', ('open', 'paid'))])
            if inv_exist:
                return (300, u"Ncf duplicado", u"Este número de comprobante ya fue registrado para este proveedor!")

            if not ncf.is_valid(invoice.move_name):
                return (500, u"Ncf invalido", u"El numero de comprobante fiscal no es valido! "
                                              u"no paso la validacion en DGII, Verifique que el NCF y el RNC del "
                                              u"proveedor esten correctamente digitados, si es de proveedor informal o de "
                                              u"gasto menor vefifique si debe solicitar nuevos numero.")

        return True

    def rates(self):
        request_params = self.get_marcos_api_request_params()
        if request_params[0] == 1:
            return requests.get("{}/rates".format(request_params[1], proxies=request_params[2])).json()

    def central_bank_rates(self):
        request_params = self.get_marcos_api_request_params()
        if request_params[0] == 1:
            return requests.get("{}/central_bank_rates".format(request_params[1], proxies=request_params[2])).json()

    @api.multi
    def cron_auto_update_rates(self):
        try:
            usd = self.central_bank_rates()
            currency_id = self.env.ref("base.USD")
            if usd.get("dollar"):
                if usd["dollar"].get("selling_rate") and currency_id:
                    self.env["res.currency.rate"].create({"name": fields.Datetime.now(),
                                                          "rate": 1 / float(usd["dollar"]["selling_rate"]),
                                                          "currency_id": currency_id.id,
                                                          "company_id": self.env.user.id})
        except Exception as err:
            _logger.warning("call api.marcos.do raise {}".format(err))
