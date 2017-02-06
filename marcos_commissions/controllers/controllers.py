# -*- coding: utf-8 -*-
from openerp import http

# class MarcosCommissions(http.Controller):
#     @http.route('/marcos_commissions/marcos_commissions/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/marcos_commissions/marcos_commissions/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('marcos_commissions.listing', {
#             'root': '/marcos_commissions/marcos_commissions',
#             'objects': http.request.env['marcos_commissions.marcos_commissions'].search([]),
#         })

#     @http.route('/marcos_commissions/marcos_commissions/objects/<model("marcos_commissions.marcos_commissions"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('marcos_commissions.object', {
#             'object': obj
#         })