# -*- coding: utf-8 -*-
from openerp import http

# class NcfCjc(http.Controller):
#     @http.route('/ncf_cjc/ncf_cjc/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ncf_cjc/ncf_cjc/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ncf_cjc.listing', {
#             'root': '/ncf_cjc/ncf_cjc',
#             'objects': http.request.env['ncf_cjc.ncf_cjc'].search([]),
#         })

#     @http.route('/ncf_cjc/ncf_cjc/objects/<model("ncf_cjc.ncf_cjc"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ncf_cjc.object', {
#             'object': obj
#         })