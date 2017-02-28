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

from odoo import models, api
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):
        invoice = self._context.get('invoice', False)
        self._post_validate()

        if invoice:
            sale_fiscal_type = invoice.fiscal_position_id.sale_fiscal_type
            ncf_control = invoice.journal_id.ncf_control
            if invoice.amount_total == 0:
                raise ValidationError(
                    u"¡No puede validar una factura con valor 0!")
            if invoice.type in ('out_invoice', 'out_refund') and ncf_control is True:
                if not sale_fiscal_type:
                    raise ValidationError(
                        u"Debe especificar el tipo de comprobante para la"
                        " venta.")
                if (sale_fiscal_type != 'final' and
                   not invoice.partner_id.vat):
                    raise ValidationError(
                        u"Para este tipo de posición fiscal el Contacto"
                        " debe de tener un RNC establecido!")

                if not invoice.move_name:
                    if invoice.type == "out_refund":
                        sequence = invoice.shop_id.nc_sequence_id
                    elif sale_fiscal_type == "final":
                        sequence = invoice.shop_id.final_sequence_id
                    elif sale_fiscal_type == "fiscal":
                        sequence = invoice.shop_id.fiscal_sequence_id
                    elif sale_fiscal_type == "gov":
                        sequence = invoice.shop_id.gov_sequence_id
                    elif sale_fiscal_type == "special":
                        sequence = invoice.shop_id.special_sequence_id

                    invoice.shop_id.check_max(sale_fiscal_type,
                                              invoice)
                    invoice.move_name = sequence.with_context(
                            ir_sequence_date=invoice.date_invoice).next_by_id()
                    invoice.reference = invoice.journal_id.sequence_id.with_context(ir_sequence_date=invoice.date_invoice).next_by_id()
        return super(AccountMove, self).post()
