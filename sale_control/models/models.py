# -*- coding: utf-8 -*-
from openerp import api, models, fields, SUPERUSER_ID


class pos_config(models.Model):
    _inherit = 'res.users'

    allow_payments = fields.Boolean('Permitir cobrar', default=True)
    allow_delete_order = fields.Boolean('Allow remove non-empty order', default=True)
    allow_discount = fields.Float('Maximo descuento permitido en (%)', default=0)
    allow_edit_price = fields.Boolean('Permitir cambiar el precio', default=True)
    allow_delete_order = fields.Boolean('Permitir eliminar orde no vacías en el POS', default=True)
    allow_refund = fields.Boolean("Permitir hacer devoluciones", default=False)
    allow_delete_order_line = fields.Boolean('Permitir eliminar línea de la orden', default=True)
    allow_cancel = fields.Boolean("Pueden cancelar ordenes nuevas")
    allow_cash_refund = fields.Boolean("Permitir devolver dinero de la caja", default=False)
    allow_credit = fields.Boolean("Permitir facturar a credito", default=False)






