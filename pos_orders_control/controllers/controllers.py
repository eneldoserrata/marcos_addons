# -*- coding: utf-8 -*-
from openerp import http

# class PosOrdersControl(http.Controller):
#     @http.route('/pos_orders_control/pos_orders_control/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_orders_control/pos_orders_control/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_orders_control.listing', {
#             'root': '/pos_orders_control/pos_orders_control',
#             'objects': http.request.env['pos_orders_control.pos_orders_control'].search([]),
#         })

#     @http.route('/pos_orders_control/pos_orders_control/objects/<model("pos_orders_control.pos_orders_control"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_orders_control.object', {
#             'object': obj
#         })