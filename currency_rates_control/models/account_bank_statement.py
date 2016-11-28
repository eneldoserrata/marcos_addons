# -*- encoding: utf-8 -*-

from openerp import models
from openerp.tools import float_compare, float_round


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _prepare_reconciliation_move_line(self, move, amount):
        res = super(AccountBankStatementLine, self)._prepare_reconciliation_move_line(move, amount)

        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency

        if not (statement_currency == company_currency) and not (st_line_currency == company_currency):
            total_amount = statement_currency.with_context({'date': self.date}).compute(self.amount, company_currency,round=False)
            if float_compare(total_amount, amount, precision_digits=company_currency.rounding) == 0:
                ratio = 1.0
            else:
                ratio = total_amount / amount
            # Then use it to adjust the statement.line field that correspond to the move.line amount_currency
            if statement_currency != company_currency:
                amount_currency = self.amount * ratio
            elif st_line_currency != company_currency:
                amount_currency = self.amount_currency * ratio

            res.update({'amount_currency': amount_currency})
            from pprint import pprint as pp
            pp(res)
            import pdb;pdb.set_trace()



