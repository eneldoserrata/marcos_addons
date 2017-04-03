# -*- coding: utf-8 -*-
from openerp import http

# class MarcosAccountReports(http.Controller):
#     @http.route('/marcos_account_reports/marcos_account_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/marcos_account_reports/marcos_account_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('marcos_account_reports.listing', {
#             'root': '/marcos_account_reports/marcos_account_reports',
#             'objects': http.request.env['marcos_account_reports.marcos_account_reports'].search([]),
#         })

#     @http.route('/marcos_account_reports/marcos_account_reports/objects/<model("marcos_account_reports.marcos_account_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('marcos_account_reports.object', {
#             'object': obj
#         })