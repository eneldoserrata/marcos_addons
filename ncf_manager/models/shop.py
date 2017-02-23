# -*- coding: utf-8 -*-
###############################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL.
#  (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it,
# unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without
# copying any source code or material from the Software. You may distribute
# those modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the
# Softwar or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

from openerp import models, fields, api, exceptions


class ShopJournalConfig(models.Model):
    _name = "shop.ncf.config"

    # #### VARIABLES DE CONFIGURACION DE LA SUCURSAL ####
    company_id = fields.Many2one("res.company", required=True,
                                 default=lambda s: s.env.user.company_id.id,
                                 string=u"Compañia")
    name = fields.Char("Nombre", size=40, required=True)
    sale_journal_ids = fields.Many2many("account.journal",
                                        string=u"Diarios de ventas",
                                        required=False,
                                        domain="[('type','=','sale')]")
    user_ids = fields.Many2many("res.users",
                                string=u"Usuarios que pueden usar esta sucursal")

    _sql_constraints = [('shop_ncf_config_name_uniq', 'unique(name)',
                         u'El nombre de la sucursal debe de ser único!')]

    # #### VARIABLES DE CONFIGURACION DE LOS COMPROBANTES FISCALES ####

    # SECUENCIA FINAL
    final_sequence_id = fields.Many2one("ir.sequence",
                                        string=u"Secuencia")
    final_number_next_actual = fields.Integer(
                            string=u"Próximo Número",
                            related="final_sequence_id.number_next_actual")
    final_max = fields.Integer(string=u"Número Máximo")

    # SECUENCIA FISCAL
    fiscal_sequence_id = fields.Many2one("ir.sequence",
                                         string=u"Secuencia")
    fiscal_number_next_actual = fields.Integer(
                            string=u"Próximo Número",
                            related="fiscal_sequence_id.number_next_actual")
    fiscal_max = fields.Integer(string=u"Número Máximo")

    # SECUENCIA GUBERNAMENTAL
    gov_sequence_id = fields.Many2one("ir.sequence",
                                      string=u"Secuencia")
    gov_number_next_actual = fields.Integer(
                            string=u"Próximo Número",
                            related="gov_sequence_id.number_next_actual")
    gov_max = fields.Integer(string=u"Número Máximo")

    # SECUENCIA ESPECIAL
    special_sequence_id = fields.Many2one("ir.sequence",
                                          string=u"Secuencia")
    special_number_next_actual = fields.Integer(
                            string=u"Próximo Número",
                            related="special_sequence_id.number_next_actual")
    special_max = fields.Integer(string=u"Número Máximo")

    # SECUENCIA NOTA DE CRÉDITO
    nc_sequence_id = fields.Many2one("ir.sequence",
                                     string=u"Secuencia")
    nc_number_next_actual = fields.Integer(
                            string=u"Próximo Número",
                            related="nc_sequence_id.number_next_actual")
    nc_max = fields.Integer(string=u"Número Máximo")

    # SECUENCIA NOTA DE DÉBITO
    nd_sequence_id = fields.Many2one("ir.sequence",
                                     string=u"Secuencia")
    nd_number_next_actual = fields.Integer(
                            string=u"Próximo Número",
                            related="nd_sequence_id.number_next_actual")
    nd_max = fields.Integer(string=u"Número Máximo")

    @api.model
    def get_user_shop_config(self):

        user_shops = self.search([('user_ids', '=', self._uid)])
        if not user_shops:
            raise exceptions.UserError("Su usuario no tiene una sucursal"
                                       " asignada.")

        return user_shops[0]

    @api.model
    def setup_ncf(self):
        self.env["account.fiscal.position"].search([]).unlink()

        fiscal_prefix = u"A0100100101"
        final_prefix = u"A0100100102"
        nd_prefix = u"A0100100103"
        nc_prefix = u"A0100100104"
        esp_prefix = u"A0100100114"
        gov_prefix = u"A0100100115"

        if not self.search([]):
            shop = self.create({"name": "Principal",
                                "journal_id": 1,
                                "user_ids": [(4, 1, False)],
                                "final_account_id": 115,
                                "fiscal_account_id": 115,
                                "gov_account_id": 115,
                                "special_account_id": 115,
                                "final_max": 100,
                                "fiscal_max": 100,
                                "gov_max": 100,
                                "special_max": 100,
                                "nc_max": 100,
                                "nd_max": 100
                                })

            seq_values = {u'padding': 8,
                          u'code': False,
                          u'name': u'Facturas de cliente final',
                          u'implementation': u'no_gap',
                          u'company_id': 1,
                          u'use_date_range': False,
                          u'number_increment': 1,
                          u'prefix': u'A0100100102',
                          u'date_range_ids': [],
                          u'number_next_actual': 1,
                          u'active': True,
                          u'suffix': False}

            sale_journal = self.env["account.journal"].browse(1)
            sale_journal.ncf_control = True

            seq_values["prefix"] = final_prefix
            seq_values["name"] = "Facturas para Consumidores Finales"
            final_id = self.env["ir.sequence"].create(seq_values)
            shop.final_sequence_id = final_id.id

            seq_values["prefix"] = fiscal_prefix
            seq_values["name"] = "Facturas con Valor Fiscal"
            fiscal_id = self.env["ir.sequence"].create(seq_values)
            shop.fiscal_sequence_id = fiscal_id.id

            seq_values["prefix"] = gov_prefix
            seq_values["name"] = "Facturas Gubernamentales"
            gov_id = self.env["ir.sequence"].create(seq_values)
            shop.gov_sequence_id = gov_id.id

            seq_values["prefix"] = esp_prefix
            seq_values["name"] = u"Facturas de Regímenes Especiales"
            esp_id = self.env["ir.sequence"].create(seq_values)
            shop.special_sequence_id = esp_id.id

            seq_values["prefix"] = nc_prefix
            seq_values["name"] = u"Notas de Crédito"
            nc_id = self.env["ir.sequence"].create(seq_values)
            shop.refund_sequence_id = nc_id.id
            shop.nc_sequence_id = nc_id.id

            seq_values["prefix"] = nd_prefix
            seq_values["name"] = u"Notas de Débito"
            nd_id = self.env["ir.sequence"].create(seq_values)
            shop.nd_sequence_id = nd_id.id

    def check_max(self, sale_fiscal_type, invoice):
        message = False

        if invoice.type == "out_refund" and self.nc_max >= self.nc_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Notas de Crédito para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "final" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Consumidor Final para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "fiscal" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Valor Fiscal para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "gov" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias Gubernamentales para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "special" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Regímenes Esp. para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "unico" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Único Ingreso para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        if message:
            mail_details = {'subject': "NCF casi Agotados",
                            'body': message,
                            'partner_ids': [user.id for user in self.user_ids]
                            }

            invoice.message_post(type="notification", subtype="mt_comment",
                                 **mail_details)
