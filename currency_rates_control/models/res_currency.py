# -*- coding: utf-8 -*-

# NOTE: this code write by Alexis de Lattre <alexis.delattre@akretion.com> on odoo module Currency Rate Date Check


from openerp import models, fields, api



class res_currency_rate(models.Model):
    _inherit = "res.currency.rate"

    rate = fields.Float('Rate', digits=(12, 12), help='The rate of the currency to the currency of rate 1')
    name = fields.Date('Date', required=True, select=True)


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def _get_rate(self, rate_date=False):
        if rate_date:
            self._cr.execute("""SELECT rate FROM res_currency_rate
                               WHERE currency_id = %s
                                 AND name = %s
                                 AND (company_id is null
                                     OR company_id = %s)
                            ORDER BY company_id, name desc LIMIT 1""",
                           (self.id, rate_date, self.env.user.company_id.id))
            if self._cr.rowcount > 0:
                return (1 / self._cr.fetchone()[0])

        return False