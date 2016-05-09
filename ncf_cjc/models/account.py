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
    statement_id = fields.Many2one("account.bank.statement", string="Caja Chica")

    @api.constrains("partner_id")
    def partner_contraing(self):
        if self.payment_type == "cjc":
            employee_id = self.env["hr.employee"].search([('address_home_id', '=', self.partner_id.id)])
            if not employee_id:
                raise exceptions.ValidationError(u"Este proveedor no esta relacionado a un empleado,"
                                                 u"en el registro de el empleado favor de completar en campo"
                                                 u"Dirección particular en la prestaña de información personal.")

    @api.multi
    def pre_post(self):

        for rec in self:
            if rec.petty_cash == True:
                employee_id = self.env["hr.employee"].search([('address_home_id', '=', rec.partner_id.id)])
                count_open_statement = self.env["account.bank.statement"].search_count(
                    [('state', '=', 'open'), ('employee_id', '=', employee_id.id)])
                if count_open_statement >= employee_id.multi_petty_cash:
                    raise exceptions.ValidationError("Este empleado ya tiene {} caja chica abierta, "
                                                     "Para poder generar el remmbolso primero deberia cerrarla".format(
                        count_open_statement))

                new_statement = self.env["account.bank.statement"].create({"journal_id": rec.cjc_journal_id.id,
                                                                           "balance_start": rec.amount,
                                                                           "employee_id": employee_id.id})
                new_cjc = self.env["hr.cjc"].create({"statement_id": new_statement.id,
                                                     "employye_id": employee_id.id,
                                                     "name": self.env['ir.sequence'].get('cjc')})

                new_statement.write({"cjc_id": new_cjc.id})
                rec.communication = "Rembolso de caja chica {} ".format(new_statement.name)
                rec.statement_id = new_statement.id

        self.post()

        for rec in self:
            if rec.petty_cash == True:

                move_line_ids = self.env["account.move.line"].search([('payment_id','=',rec.id)])

                if move_line_ids:
                    to_reconcile = [move_line.id for move_line in move_line_ids if move_line.debit > 0]
                    move_id = move_line_ids[0].move_id
                    cjc_acount_move = move_id.copy({"journal_id": rec.cjc_journal_id.id})
                    for line in cjc_acount_move.line_ids:
                        if line.credit > 0:
                            line.write({"account_id": rec.partner_id.property_account_payable_id.id,
                                        "journal_id": rec.cjc_journal_id.id,
                                        "ref": rec.communication})
                            to_reconcile.append(line.id)
                        else:
                            line.write({"account_id": rec.cjc_journal_id.default_debit_account_id.id,
                                        "journal_id": rec.cjc_journal_id.id,
                                        "ref": rec.communication})
                    cjc_acount_move.post()
                    self.env["account.move.line"].browse(to_reconcile).reconcile()


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    employee_id = fields.Many2one("hr.employee", string="Empleado")
    petty_cash = fields.Boolean("se puede usar en caja chica", default=False, related="journal_id.petty_cash")
    cjc_id = fields.Many2one("hr.cjc", string=u"Relación de gastos")
