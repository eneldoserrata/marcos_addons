# -*- coding: utf-8 -*-
from odoo import http

# class PreventNameDuplicate(http.Controller):
#     @http.route('/prevent_name_duplicate/prevent_name_duplicate/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prevent_name_duplicate/prevent_name_duplicate/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('prevent_name_duplicate.listing', {
#             'root': '/prevent_name_duplicate/prevent_name_duplicate',
#             'objects': http.request.env['prevent_name_duplicate.prevent_name_duplicate'].search([]),
#         })

#     @http.route('/prevent_name_duplicate/prevent_name_duplicate/objects/<model("prevent_name_duplicate.prevent_name_duplicate"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prevent_name_duplicate.object', {
#             'object': obj
#         })