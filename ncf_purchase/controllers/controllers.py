# -*- coding: utf-8 -*-
from openerp import http

# class NcfPurchase(http.Controller):
#     @http.route('/ncf_purchase/ncf_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ncf_purchase/ncf_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ncf_purchase.listing', {
#             'root': '/ncf_purchase/ncf_purchase',
#             'objects': http.request.env['ncf_purchase.ncf_purchase'].search([]),
#         })

#     @http.route('/ncf_purchase/ncf_purchase/objects/<model("ncf_purchase.ncf_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ncf_purchase.object', {
#             'object': obj
#         })