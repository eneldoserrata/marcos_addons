# -*- coding: utf-8 -*-

from openerp import fields, models, api, exceptions

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    cjc_journal_ids = fields.Many2many("account.journal", string="Diarios permitidos en caja chica", domain=[('petty_cash','=',True)])
    multi_petty_cash = fields.Integer("Numero de caja chica permitidas", default=1)


class HrCjc(models.Model):
    _name = 'hr.cjc'

    @api.model
    def _get_employee(self):
        employee_id = self.env.user.employee_ids #TODO fix
        if employee_id:
            return self.env.user.employee_ids.id
        else:
            raise exceptions.ValidationError("Su usuario no esta vinculado a un empleado.")

    @api.model
    @api.depends("employee_id")
    def _get_statement(self):
        pass

    name = fields.Char("Numero")
    statement_id = fields.Many2one("account.bank.statement", string="Control de efetivo", deafult=_get_statement, readonly=True)
    journal_id = fields.Many2one("account.journal", related="statement_id.journal_id")
    employee_id = fields.Many2one("hr.employee", string="Empleado", default=_get_employee, readonly=True)
    start_date = fields.Date("Fecha del Desembolso", default=fields.Date.today(), required=True)
    end_date = fields.Date("Fecha de cierre", required=False)
    expense_ids = fields.One2many("hr.expense", "cjc_id")


class HrExpense(models.Model):
    _inherit = "hr.expense"

    cjc_id = fields.Many2one("hr.cjc")
    account_fiscal_id = fields.Many2one("account.fiscal.position", string=u"Posición fiscal")
    invoice_id = fields.Many2one("account.invoice", string="Factura")
    partner_id = fields.Many2one("re.partner", string="Proveedor")
    fiscal_posistion_id = fields.Many2one("account.fiscal.position", string="Tipo de gasto",
                                          domain=[('supplier', '=', True)])
    line_ids = fields.One2many("hr.expense.line", "expense_id")
    product_id = fields.Many2one('product.product', string='Product', readonly=True, states={'draft': [('readonly', False)]}, domain=[('can_be_expensed', '=', True)], required=False)
    ncf = fields.Char("NCF", size=19)



class HrExpenseLine(models.Model):
    _name = "hr.expense.line"

    @api.model
    def _compute_amount(self):
        self.amount_total = 0;
        for line in self.line_ids:
            self.amount_total += line.amount

    expense_id = fields.Many2one("hr.expense")
    product_id = fields.Many2one("product.product", string="Producto")
    name = fields.Char(u"Descripción", required=True)
    quantity = fields.Float("Cantidad", required=True, deafult=1)
    price = fields.Float("Precio", required=True)
    amount = fields.Float(compute=_compute_amount, string="Total")






