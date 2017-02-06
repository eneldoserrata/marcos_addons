class AccountAccount(models.Model):
    _name = "account.account"
    _description = "Account"
    _order = "code"

    #@api.multi
    #def _compute_has_unreconciled_entries(self):
    #    print "ici dedans"
    #    account_ids = self.ids
    #    for account in self:
    #        # Avoid useless work if has_unreconciled_entries is not relevant for this account
    #        if account.deprecated or not account.reconcile:
    #            account.has_unreconciled_entries = False
    #            account_ids = account_ids - account
    #    if account_ids:
    #        res = dict.fromkeys([x.id for x in account_ids], False)
    #        self.env.cr.execute(
    #            """ SELECT s.account_id FROM(
    #                    SELECT
    #                        a.id as account_id, a.last_time_entries_checked AS last_time_entries_checked,
    #                        MAX(l.write_date) AS max_date
    #                    FROM
    #                        account_move_line l
    #                        RIGHT JOIN account_account a ON (a.id = l.account_id)
    #                    WHERE
    #                        a.id in %s
    #                        AND EXISTS (
    #                            SELECT 1
    #                            FROM account_move_line l
    #                            WHERE l.account_id = a.id
    #                            AND l.amount_residual > 0
    #                        )
    #                        AND EXISTS (
    #                            SELECT 1
    #                            FROM account_move_line l
    #                            WHERE l.account_id = a.id
    #                            AND l.amount_residual < 0
    #                        )
    #                    GROUP BY a.id, a.last_time_entries_checked
    #                ) as s
    #                WHERE (last_time_entries_checked IS NULL OR max_date > last_time_entries_checked)
    #            """ % (account_ids,))
    #        res.update(self.env.cr.dictfetchall())
    #        for account in self.browse(res.keys()):
    #            if res[account.id]:
    #                account.has_unreconciled_entries = True

    @api.multi
    @api.constrains('internal_type', 'reconcile')
    def _check_reconcile(self):
        for account in self:
            if account.internal_type in ('receivable', 'payable') and account.reconcile == False:
                raise ValidationError(_('You cannot have a receivable/payable account that is not reconciliable. (account code: %s)') % account.code)

    name = fields.Char(required=True, index=True)
    currency_id = fields.Many2one('res.currency', string='Account Currency',
        help="Forces all moves for this account to have this account currency.")
    code = fields.Char(size=64, required=True, index=True)
    deprecated = fields.Boolean(index=True, default=False)
    user_type_id = fields.Many2one('account.account.type', string='Type', required=True, oldname="user_type",
        help="Account Type is used for information purpose, to generate country-specific legal reports, and set the rules to close a fiscal year and generate opening entries.")
    internal_type = fields.Selection(related='user_type_id.type', string="Internal Type", store=True, readonly=True)
    #has_unreconciled_entries = fields.Boolean(compute='_compute_has_unreconciled_entries',
    #    help="The account has at least one unreconciled debit and credit since last time the invoices & payments matching was performed.")
    last_time_entries_checked = fields.Datetime(string='Latest Invoices & Payments Matching Date', readonly=True, copy=False,
        help='Last time the invoices & payments matching was performed on this account. It is set either if there\'s not at least '\
        'an unreconciled debit and an unreconciled credit Or if you click the "Done" button.')
    reconcile = fields.Boolean(string='Allow Reconciliation', default=False,
        help="Check this box if this account allows invoices & payments matching of journal items.")
    tax_ids = fields.Many2many('account.tax', 'account_account_tax_default_rel',
        'account_id', 'tax_id', string='Default Taxes')
    note = fields.Text('Internal Notes')
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.account'))
    tag_ids = fields.Many2many('account.account.tag', 'account_account_account_tag', string='Tags', help="Optional tags you may want to assign for custom reporting")

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the account must be unique per company !')
    ]

    @api.model
    def default_get(self, default_fields):
        """If we're creating a new account through a many2one, there are chances that we typed the account code
        instead of its name. In that case, switch both fields values.
        """
        default_name = self._context.get('default_name')
        default_code = self._context.get('default_code')
        if default_name and not default_code:
            try:
                default_code = int(default_name)
            except ValueError:
                pass
            if default_code:
                default_name = False
        contextual_self = self.with_context(default_name=default_name, default_code=default_code)
        return super(AccountAccount, contextual_self).default_get(default_fields)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()

    @api.onchange('internal_type')
    def onchange_internal_type(self):
        if self.internal_type in ('receivable', 'payable'):
            self.reconcile = True

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for account in self:
            name = account.code + ' ' + account.name
            result.append((account.id, name))
        return result

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('code', _("%s (copy)") % (self.code or ''))
        return super(AccountAccount, self).copy(default)

    @api.multi
    def write(self, vals):
        # Dont allow changing the company_id when account_move_line already exist
        if vals.get('company_id', False):
            move_lines = self.env['account.move.line'].search([('account_id', 'in', self.ids)], limit=1)
            for account in self:
                if (account.company_id.id <> vals['company_id']) and move_lines:
                    raise UserError(_('You cannot change the owner company of an account that already contains journal items.'))
        # If user change the reconcile flag, all aml should be recomputed for that account and this is very costly.
        # So to prevent some bugs we add a constraint saying that you cannot change the reconcile field if there is any aml existing
        # for that account.
        if vals.get('reconcile'):
            move_lines = self.env['account.move.line'].search([('account_id', 'in', self.ids)], limit=1)
            if len(move_lines):
                raise UserError(_('You cannot change the value of the reconciliation on this account as it already has some moves'))
        return super(AccountAccount, self).write(vals)

    @api.multi
    def unlink(self):
        if self.env['account.move.line'].search([('account_id', 'in', self.ids)], limit=1):
            raise UserError(_('You cannot do that on an account that contains journal items.'))
        #Checking whether the account is set as a property to any Partner or not
        values = ['account.account,%s' % (account_id,) for account_id in self.ids]
        partner_prop_acc = self.env['ir.property'].search([('value_reference', 'in', values)], limit=1)
        if partner_prop_acc:
            raise UserError(_('You cannot remove/deactivate an account which is set on a customer or vendor.'))
        return super(AccountAccount, self).unlink()

    @api.multi
    def mark_as_reconciled(self):
        return self.write({'last_time_entries_checked': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

    @api.multi
    def action_open_reconcile(self):
        self.ensure_one()
        # Open reconciliation view for this account
        if self.internal_type == 'payable':
            action_context = {'show_mode_selector': False, 'mode': 'suppliers'}
        elif self.internal_type == 'receivable':
            action_context = {'show_mode_selector': False, 'mode': 'customers'}
        else:
            action_context = {'show_mode_selector': False, 'account_ids': [self.id,]}
        return {
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
            'context': action_context,
        }