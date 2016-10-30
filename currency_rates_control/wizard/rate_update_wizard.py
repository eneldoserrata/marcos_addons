# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

import logging

_logger = logging.getLogger(__name__)


class RateUpdateWizard(models.TransientModel):
    _name = "update.rate.wizard"

    def _get_currency_domain(self):
        return [('id','!=',self.env.user.company_id.currency_id.id)]

    update_method = fields.Selection([('server',u'Desde internet actualizar la tasa de hoy.'),('manual','Introducir tasa manualmente')],
                                   string=u"Metodo de actualizaciónn de tasa", default="manual")
    name = fields.Date("Fecha", required=False)
    rate = fields.Float("Monto", required=False)
    currency_id = fields.Many2one("res.currency", string="Moneda", required=False, domain=_get_currency_domain)


    @api.multi
    def update_rate(self):
        if self.update_method == "manual":
            if self.rate < 1:
                raise exceptions.UserError("El valor de la tasa debe de ser mayor que 0")
            rate = self.env["res.currency.rate"].search([('name','=',self.name),('currency_id','=',self.currency_id.id)])
            if rate:
                return rate.write({"rate": 1/self.rate})
            else:
                return self.env["res.currency.rate"].create({"name": self.name, "rate": 1/self.rate, "currency_id": self.currency_id.id})
        else:
            try:
                self.env.user.company_id.button_refresh_currency()
            except Exception as e:
                _logger.error("{}".format(e))
                raise exceptions.ValidationError("Ocurrio un error al intentar actualizar la tasa desde el servidor de internet.")



