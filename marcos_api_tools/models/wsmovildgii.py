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

from odoo import models, api
from zeep import Client


class WSMovilDGII(models.TransientModel):
    _name = "wsmovildgii"

    def getClient(self, ws):
        return Client(ws)

    def GetContribuyentes(self, value, patronBusqueda=0, inicioFilas=0, filaFilas=100, IMEI="public"):
        ws = "http://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?op=GetContribuyentes"
        client = Client(ws)
        res = client.service.GetContribuyentes(value, patronBusqueda=patronBusqueda, inicioFilas=inicioFilas,
                                               filaFilas=filaFilas, IMEI=IMEI)

    def GetContribuyentesCount(self, value, IMEI="public"):
        ws = "http://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?op=GetContribuyentesCount"
        client = Client(ws)
        res = client.service.GetContribuyentesCount(value,  IMEI=IMEI)

    def GetDocumento(self, codigoBusqueda, patronBusqueda=0, IMEI="public"):
        ws = "http://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?op=GetDocumento"
        client = Client(ws)
        res = client.service.GetDocumento(codigoBusqueda, patronBusqueda=patronBusqueda, IMEI=IMEI)

    def GetNCF(self, RNC, NCF, IMEI="public"):
        ws = "http://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?op=GetNCF"
        client = Client(ws)
        res = client.service.GetNCF(RNC, NCF, IMEI=IMEI)

    def GetPlaca(self, RNC, Placa, IMEI="public"):
        ws = "http://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?op=GetPlaca"
        client = Client(ws)
        res = client.service.GetPlaca(RNC, Placa, IMEI=IMEI)

    def GetVehiculoPorDATAMATRIX(self, value, IMEI="public"):
        ws = "http://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?op=GetVehiculoPorDATAMATRIX"
        client = Client(ws)
        res = client.service.GetVehiculoPorDATAMATRIX(value, IMEI=IMEI)
