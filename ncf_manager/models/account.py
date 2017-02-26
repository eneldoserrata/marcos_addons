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

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    purchase_fiscal_type = fields.Selection(
        [("normal", u"Requiere NCF"),
         ("minor", u"Gasto Menor. NCF Generado por el Sistema"),
         ("informal", u"Proveedores Informales. NCF Generado por el Sistema"),
         ("exterior", u"Pagos al Exterior. NCF Generado por el Sistema"),
         ("import", u"Importaciones. NCF Generado por el Sistema"),
         ("others", u"Otros. No requiere NCF")],
        string=u"Tipo de Compra", default="normal",
         )

    ncf_control = fields.Boolean("Control de NCF")
    ncf_remote_validation = fields.Boolean(u"Validar con DGII", default=True)


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    supplier = fields.Boolean("Para proveedores")

    sale_fiscal_type = fields.Selection(
        [("final", u"Consumidor final"),
         ("fiscal", u"Para Crédito Fiscal"),
         ("gov", u"Gubernamental"),
         ("special", u"Regímenes Especiales"),
         ("unico", u"Único Ingreso")],
        string="Tipo de Comprobante"
        )

    journal_id = fields.Many2one(
        "account.journal", string="Diario de Compras",
        domain="[('type','=','purchase')]")


class AccountTax(models.Model):
    _inherit = 'account.tax'

    purchase_tax_type = fields.Selection(
        [('itbis', 'ITBIS Pagado'),
         ('ritbis', 'ITBIS Retenido'),
         ('isr', 'ISR Retenido'),
         ('cost', 'Forma Parte del Gasto'),
         ('none', 'No Deducible')],
        default="itbis", string="Tipo de Impuesto de Compra"
        )
