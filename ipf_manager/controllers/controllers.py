# -*- coding: utf-8 -*-
from openerp import http

# class IpfManager(http.Controller):
#     @http.route('/ipf_manager/ipf_manager/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ipf_manager/ipf_manager/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ipf_manager.listing', {
#             'root': '/ipf_manager/ipf_manager',
#             'objects': http.request.env['ipf_manager.ipf_manager'].search([]),
#         })

#     @http.route('/ipf_manager/ipf_manager/objects/<model("ipf_manager.ipf_manager"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ipf_manager.object', {
#             'object': obj
#         })