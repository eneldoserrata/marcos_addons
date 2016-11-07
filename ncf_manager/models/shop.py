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

    company_id = fields.Many2one("res.company", required=True,
                                 default=lambda s: s.env.user.company_id.id,
                                 string=u"Compañia"
                                 )
    name = fields.Char("Nombre", size=40, required=True)
    sale_journal_ids = fields.Many2many("account.journal",
                                        string=u"Diarios de ventas",
                                        required=False,
                                        domain="[('type','=','sale')]"
                                        )
    user_ids = fields.Many2many("res.users",
                                string=u"Usuarios con acceso a esta sucursal")

    _sql_constraints = [
     ('shop_ncf_config_name_uniq', 'unique(name)',
      u'El nombre de la sucursal debe de ser único!'),
    ]

    @api.model
    def get_user_shop_config(self):
        if self._context.get("module", False) == "ncf_manager":
            if not self.search([]):
                self.create({"name": "Principal",
                             "sale_journal_ids": [(4, 1, False)],
                             "user_ids": [(4, 1, False)]}
                            )

        user_shops = self.search([('user_ids', '=', self._uid)])
        if not user_shops:
            raise exceptions.UserError("Su usuario no tiene una sucursal"
                                       " asignada.")

        if self._context.get("module", False) == "ncf_manager":
            shop_ids = [rec for rec in user_shops]
        else:
            shop_ids = [rec.id for rec in user_shops]

        sale_journal_ids = list(
                                set(sum([[sale_journal_id.id for
                                    sale_journal_id in rec.sale_journal_ids]
                                    for rec in user_shops], []))
                                )

        if not sale_journal_ids:
            raise exceptions.UserError("Su sucursal no tiene asignada Diarios"
                                       " de Facturas asignadas.")

        return {"shop_ids": shop_ids, "sale_journal_ids": sale_journal_ids}
