# -*- coding: utf-8 -*-
from openerp import http

# class PosManager(http.Controller):
#     @http.route('/pos_manager/pos_manager/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_manager/pos_manager/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_manager.listing', {
#             'root': '/pos_manager/pos_manager',
#             'objects': http.request.env['pos_manager.pos_manager'].search([]),
#         })

#     @http.route('/pos_manager/pos_manager/objects/<model("pos_manager.pos_manager"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_manager.object', {
#             'object': obj
#         })