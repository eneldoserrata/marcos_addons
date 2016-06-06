# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    petty_cash = fields.Boolean("se puede usar en caja chica", default=False)

    @api.onchange("type")
    def onchange_petty_cash(self):
        if self.type not in ['cash', 'purchase']:
            self.petty_cash = False


class account_payment(models.Model):
    _inherit = "account.payment"

    petty_cash = fields.Boolean(string='Rembolso de caja chica')
    cjc_journal_id = fields.Many2one("account.journal", string="Diario de caja chica",
                                     domain=[('type', '=', 'cash'), ('petty_cash', '=', True)])
    statement_id = fields.Many2one("account.bank.statement", string="Caja Chica", readonly=True, states={'draft': [('readonly', False)]})

    @api.multi
    def post(self):
        super(account_payment, self).post()
        if self.petty_cash:
            employee_id = self.env["hr.employee"].search([('address_home_id','=',self.partner_id.id)])
            statement_id =  self.env["account.bank.statement"].create({
                "journal_id": self.cjc_journal_id.id,
                "employee_id": employee_id.id,
                "balance_start": self.amount,
                "date": self.payment_date,
                "state": "cjc"
            })
            self.communication = "Rembolso de caja chica"
            self.statement_id = statement_id.id

    def _get_counterpart_move_line_vals(self, invoice=False):
        res = super(account_payment, self)._get_counterpart_move_line_vals(invoice=invoice)
        if self.petty_cash:
            employee_id = self.env["hr.employee"].search([('address_home_id','=',self.partner_id.id)])
            if not employee_id:
                raise exceptions.ValidationError(u"Debe indicar la Dirección particular del empleado en la pestaña de información personal")
            account_id = self.cjc_journal_id.default_debit_account_id
            if not account_id:
                raise exceptions.ValidationError("Debe especificar la cuenta de debito del diario de caja chica")
            res.update({"account_id": account_id.id,
                        "name": "Rembolso de caja chica"})
        return res

    @api.multi
    def cancel(self):
        for rec in self:
            if rec.statement_id and rec.statement_id.state == "confirm":
                raise exceptions.ValidationError(u"No puede cancelar esta transacción por que esta vinculada a una caja chica validada!")
            if rec.statement_id:
                rec.statement_id.state = "open"
                rec.statement_id.unlink()
        super(account_payment, self).cancel()


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    employee_id = fields.Many2one("hr.employee", string="Empleado", states={'confirm': [('readonly', True)], 'cjc': [('readonly', True)]})
    petty_cash = fields.Boolean("se puede usar en caja chica", default=False, related="journal_id.petty_cash")
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    state = fields.Selection([('open', 'New'), ("cjc", "Caja chica abierta"), ('confirm', 'Validated')], string='Status', required=True, readonly=True, copy=False, default='open')

    @api.onchange("petty_cash")
    def onchange_pretty_cash(self):
        if not self.petty_cash:
            self.employee_id = False

    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'account.bank.statement'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)


    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'account.bank.statement'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'account.bank.statement', 'default_res_id': self.id}
        return res


class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"


    invoice_id = fields.Many2one("account.invoice", "Factura", copy=False)


    @api.multi
    def view_invoice(self):
        for record in self:

            view_ref = self.pool.get('ir.model.data').get_object_reference('account', 'invoice_supplier_form')
            view_id = view_ref[1] if view_ref else False

            res = {
                'type': 'ir.actions.act_window',
                'name': 'Supplier Invoice',
                'res_model': 'account.invoice',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'new',
                "res_id": record.invoice_id.id,
            }

            return res