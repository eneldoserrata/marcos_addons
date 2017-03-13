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
from odoo import models, fields, api


class CheckReportConfig(models.Model):
    _name = "check.report.config"

    name = fields.Char("Nombre", required=True)

    font_zise = fields.Float(string=u"Tamaño del las letras", default=15)
    body_top = fields.Float(string="Margen superior del cuerpo del cheque", default=23)

    date_top = fields.Float(string="Margen superior de la fecha", default=4.2)
    date_left = fields.Float(string="Margen izquierdo de la fecha" , default=202)

    name_top = fields.Float(string="Margen superior del nombre", default=21)
    name_left = fields.Float(string="Margen izquierdo del nombre", default=57)

    amount_top = fields.Float(string="Margen superior del monto", default=20)
    amount_left = fields.Float(string="Margen izquierdo del monto", default=192)

    amount_letter_top = fields.Float(string="Margen superior monto en letras", default=31)
    amount_letter_left = fields.Float(string="Margen izquierdo monto en letras", default=20)

    check_header_top = fields.Float("Margen superior de la Cabecera", default=0)
    check_header_left = fields.Float("Margen izquierdo de la Cabecera", default=0)
    check_header = fields.Many2one("ir.ui.view", string="Plantilla Cabecera del cheque")

    check_footer_top = fields.Float("Margen superior del pie", default=130)
    check_footer_left = fields.Float("Margen izquierdo del pie", default=3)
    check_footer = fields.Many2one("ir.ui.view", string="Plantilla Pie del cheque")
