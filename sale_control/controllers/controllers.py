# -*- coding: utf-8 -*-
from openerp import http

# class SaleControl(http.Controller):
#     @http.route('/sale_control/sale_control/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_control/sale_control/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_control.listing', {
#             'root': '/sale_control/sale_control',
#             'objects': http.request.env['sale_control.sale_control'].search([]),
#         })

#     @http.route('/sale_control/sale_control/objects/<model("sale_control.sale_control"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_control.object', {
#             'object': obj
#         })