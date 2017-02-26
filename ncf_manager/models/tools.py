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
from odoo import models, fields, api, exceptions


def is_ncf(value):
    u"""
    Valida estructura del Número de Comprobante Ficasl (NCF)
    para República Dominicana.

    Caracter 1: Serie
        Valores Permitidos: A o P
    Caracter 2-3: División de Negocios
        Valores Permitidos: 1 al 99
    Caracter 4-6: Punto de Emisión
        Valores Permitidos: 1 al 999
    Caracter 7-9: Area de Impresión
        Valores Permitidos: 1 al 999
    Caracter 10-11: Tipo de Comprobante 
        Valores Permitidos: 01, 02, 03, 04, 11, 12, 13, 14, 15
    Caracter 12-19: Secuendial
        Valores Permitidos: 1 al 99,999,999 (sin comas)
        
    Tamaño: 19 Caracteres

    :param value: string con NCF

    :returns: True cuando tiene exito, False cuando falla.
    """

    if len(value) == 19:
        try:
            if value[0] in ('A', 'P') and int(value[1:3]) and int(value[3:6]) and int(value[6:9])\
                    and value[9:11] == '01' and int(
                    value[11:20]):
                return True
        except:
            pass
    return False
