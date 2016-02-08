# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError

# class SaleAdvancePaymentInv(models.TransientModel):
#     _inherit = "sale.advance.payment.inv"
#
#     @api.multi
#     def _create_invoice(self, order, so_line, amount):
#         res = super(SaleAdvancePaymentInv)._create_invoice(order, so_line, amount)
#         res._onchange_partner_id()
#         res.onchange_fiscal_position_id()
#         return res



