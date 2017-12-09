# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    allow_payments = fields.Boolean(u'Permitir pagos', default=False)
    allow_delete_order = fields.Boolean(u'Permitir eliminar ordenes no vacía', default=False)
    allow_add_order = fields.Boolean(u'Permitir crear ordenes', default=False)
    allow_discount = fields.Boolean(u'Permitir descuento', default=False)
    allow_edit_price = fields.Boolean(u'Permitir la edición del precio', default=False)
    allow_decrease_amount = fields.Boolean(u'Permitir la edición de la cantidad', default=False)
    allow_delete_order_line = fields.Boolean(u'Permitir eliminar línea de pedido', default=False)
    allow_create_order_line = fields.Boolean(u'Permitir crear línea de pedido', default=False)
    allow_refund_order = fields.Boolean(u'Permitir crear notas de crédito', default=False)
    can_refund_money = fields.Boolean(u"Sacar dinero solo con nota de crédito.", default=False)
