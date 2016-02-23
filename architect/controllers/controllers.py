# -*- coding: utf-8 -*-
from openerp import http

# class Architect(http.Controller):
#     @http.route('/architect/architect/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/architect/architect/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('architect.listing', {
#             'root': '/architect/architect',
#             'objects': http.request.env['architect.architect'].search([]),
#         })

#     @http.route('/architect/architect/objects/<model("architect.architect"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('architect.object', {
#             'object': obj
#         })