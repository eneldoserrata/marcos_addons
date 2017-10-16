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
{
    'name': "Controlador para impresoras fiscales Dominicana",

    'summary': """
        Localizacion Para Republica Dominicana
        Controlador para impresoras fiscales EPSON TM-T88v.
    """,

    'description': """
        Este modulo permite que odoo pueda imprimir desde el modulo de punto de venta y el modulo de contabilidad
        en la impresora fiscal EPSON TM-T88v utilizando una interface fiscal desarrollada por nuestra empresa.
    """,

    'author': "Marcos Organizador de Negocios SRL - Write by Eneldo Serrata",
    'website': "http://marcos.do",
    'category': 'Uncategorized',
    'version': '10.0',
    'depends': ['base', 'web', 'account','point_of_sale','marcos_api_tools'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/ipf_view.xml',
        'views/account_view.xml',
        'views/account_invoice_view.xml',
        'views/pos_config_view.xml'

    ],
    # only loaded in demonstration mode
    'qweb': ['static/src/xml/ipf_manager.xml'],
    'demo': [
        'demo/demo.xml',
    ],
    'license': "Other proprietary",
    "price": 50,
    'currency': 'EUR'
}
