# -*- coding: utf-8 -*-
from odoo import http

# class MarcosApiTools(http.Controller):
#     @http.route('/marcos_api_tools/marcos_api_tools/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/marcos_api_tools/marcos_api_tools/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('marcos_api_tools.listing', {
#             'root': '/marcos_api_tools/marcos_api_tools',
#             'objects': http.request.env['marcos_api_tools.marcos_api_tools'].search([]),
#         })

#     @http.route('/marcos_api_tools/marcos_api_tools/objects/<model("marcos_api_tools.marcos_api_tools"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('marcos_api_tools.object', {
#             'object': obj
#         })