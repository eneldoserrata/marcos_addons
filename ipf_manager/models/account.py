# -*- coding: utf-8 -*-
from openerp import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    ipf_payment_type = fields.Selection([(u'cash', u'Efectivo'),
                                              (u'Check', u'Cheque'),
                                              (u'credit_card', u'Tarjeta de crédito'),
                                              (u'debit_card', u'Tarjeta de debito'),
                                              (u'card', u'Tarjeta'),
                                              (u'coupon', u'Cupón'),
                                              (u'other', u'Otros'),
                                              (u'credit_note', u'Nota de crédito')],
                                             string=u'Formas de pago impresora fiscal', required=False, default="other",
                                             help=u"Esta configuracion se encuantra internamente en la impresora fiscal y debe de especificar esta opecion. " \
                                                  u"Esta es la forma en que la impresora fiscal registra el pago en los libros.")

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    fiscal_nif = fields.Char("NIF", default="false", copy=False)
