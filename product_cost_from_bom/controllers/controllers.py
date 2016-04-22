# -*- coding: utf-8 -*-
from openerp import http

# class ProductCostFromBom(http.Controller):
#     @http.route('/product_cost_from_bom/product_cost_from_bom/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_cost_from_bom/product_cost_from_bom/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_cost_from_bom.listing', {
#             'root': '/product_cost_from_bom/product_cost_from_bom',
#             'objects': http.request.env['product_cost_from_bom.product_cost_from_bom'].search([]),
#         })

#     @http.route('/product_cost_from_bom/product_cost_from_bom/objects/<model("product_cost_from_bom.product_cost_from_bom"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_cost_from_bom.object', {
#             'object': obj
#         })