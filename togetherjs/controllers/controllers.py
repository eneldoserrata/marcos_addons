# -*- coding: utf-8 -*-
from odoo import http

# class Togetherjs(http.Controller):
#     @http.route('/togetherjs/togetherjs/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/togetherjs/togetherjs/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('togetherjs.listing', {
#             'root': '/togetherjs/togetherjs',
#             'objects': http.request.env['togetherjs.togetherjs'].search([]),
#         })

#     @http.route('/togetherjs/togetherjs/objects/<model("togetherjs.togetherjs"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('togetherjs.object', {
#             'object': obj
#         })