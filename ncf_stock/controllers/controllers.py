# -*- coding: utf-8 -*-
from openerp import http

# class NcfStock(http.Controller):
#     @http.route('/ncf_stock/ncf_stock/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ncf_stock/ncf_stock/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ncf_stock.listing', {
#             'root': '/ncf_stock/ncf_stock',
#             'objects': http.request.env['ncf_stock.ncf_stock'].search([]),
#         })

#     @http.route('/ncf_stock/ncf_stock/objects/<model("ncf_stock.ncf_stock"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ncf_stock.object', {
#             'object': obj
#         })