# -*- coding: utf-8 -*-

from openerp import models, fields, api


class CommissionReportWizard(models.TransientModel):
    _name = "commission.report.wizard"

    start_date = fields.Date("Desde")
    end_date = fields.Date("Hasta")
    employee_ids = fields.Many2many("hr.employee",string= "Empleados")


    @api.multi
    def create_commision_report(self):
        pass