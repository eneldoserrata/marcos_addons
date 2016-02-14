# -*- coding: utf-8 -*-
from openerp import api, models, fields, SUPERUSER_ID


class pos_config(models.Model):
    _inherit = "res.users"

    allow_payments = fields.Boolean(u"Permitir cobrar", default=True)
    allow_delete_order = fields.Boolean(u"Allow remove non-empty order", default=True)
    allow_discount = fields.Float(u"Maximo descuento permitido en (%)", default=0)
    allow_edit_price = fields.Boolean(u"Permitir cambiar el precio", default=True)
    allow_delete_order = fields.Boolean(u"Permitir eliminar orde no vacías en el POS", default=True)
    allow_refund = fields.Boolean(u"Permitir hacer devoluciones", default=False)
    allow_delete_order_line = fields.Boolean(u"Permitir eliminar línea de la orden", default=True)
    allow_cancel = fields.Boolean(u"Pueden cancelar ordenes nuevas")
    allow_cash_refund = fields.Boolean(u"Permitir devolver dinero de la caja", default=False)
    allow_credit = fields.Boolean(u"Permitir facturar a credito", default=False)






