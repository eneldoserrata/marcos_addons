# -*- coding: utf-8 -*-
from odoo import http

# class NcfPosLite(http.Controller):
#     @http.route('/ncf_pos_lite/ncf_pos_lite/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ncf_pos_lite/ncf_pos_lite/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ncf_pos_lite.listing', {
#             'root': '/ncf_pos_lite/ncf_pos_lite',
#             'objects': http.request.env['ncf_pos_lite.ncf_pos_lite'].search([]),
#         })

#     @http.route('/ncf_pos_lite/ncf_pos_lite/objects/<model("ncf_pos_lite.ncf_pos_lite"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ncf_pos_lite.object', {
#             'object': obj
#         })