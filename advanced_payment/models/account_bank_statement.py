# -*- encoding: utf-8 -*-


from odoo import models
from odoo.tools import float_compare


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _prepare_reconciliation_move_line(self, move, amount):
        """ Prepare the dict of values to create the move line from a statement line.

            :param recordset move: the account.move to link the move line
            :param float amount: the amount of transaction that wasn't already reconciled
        """
        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency

        amount_currency = False
        if statement_currency != company_currency or st_line_currency != company_currency:
            # First get the ratio total mount / amount not already reconciled
            if statement_currency == company_currency:
                total_amount = self.amount
            elif st_line_currency == company_currency:
                total_amount = self.amount_currency
            else:
                total_amount = company_currency.with_context({'date': self.date}).compute(amount, statement_currency,
                                                                                          round=True)
                # total_amount = statement_currency.with_context({'date': self.date}).compute(amount, company_currency,round=False)
            if (statement_currency != company_currency) or (st_line_currency != company_currency):
                ratio = 1 / (total_amount / amount)
            elif float_compare(total_amount, amount, precision_digits=company_currency.rounding) == 0:
                ratio = 1.0
            # Then use it to adjust the statement.line field that correspond to the move.line amount_currency
            if statement_currency != company_currency:
                amount_currency = amount / ratio
            elif st_line_currency != company_currency:
                amount_currency = self.amount_currency * ratio

        return {
            'name': self.name,
            'date': self.date,
            'ref': self.ref,
            'move_id': move.id,
            'partner_id': self.partner_id and self.partner_id.id or False,
            'account_id': amount >= 0 \
                          and self.statement_id.journal_id.default_credit_account_id.id \
                          or self.statement_id.journal_id.default_debit_account_id.id,
            'credit': amount < 0 and -amount or 0.0,
            'debit': amount > 0 and amount or 0.0,
            'statement_id': self.statement_id.id,
            'journal_id': self.statement_id.journal_id.id,
            'currency_id': statement_currency != company_currency and statement_currency.id or (
                st_line_currency != company_currency and st_line_currency.id or False),
            'amount_currency': amount_currency,
        }
