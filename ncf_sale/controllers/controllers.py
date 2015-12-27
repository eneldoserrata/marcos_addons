# -*- coding: utf-8 -*-
from openerp import http

# class NcfSale(http.Controller):
#     @http.route('/ncf_sale/ncf_sale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ncf_sale/ncf_sale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ncf_sale.listing', {
#             'root': '/ncf_sale/ncf_sale',
#             'objects': http.request.env['ncf_sale.ncf_sale'].search([]),
#         })

#     @http.route('/ncf_sale/ncf_sale/objects/<model("ncf_sale.ncf_sale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ncf_sale.object', {
#             'object': obj
#         })