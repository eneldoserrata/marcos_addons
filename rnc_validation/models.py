# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013-2015 Marcos Organizador de Negocios SRL http://marcos.do
#    Write by Eneldo Serrata (eneldo@marcos.do)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv.orm import browse_null
from tools import is_identification, _internet_on
from openerp.osv import osv, fields
import requests
from openerp import api, exceptions


class res_partner(osv.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    def _check_unique_ref(self, cr, uid, ids, context=None):
        partner = self.browse(cr, uid, ids, context=context)[0]
        if partner.customer or partner.supplier:
            if not self.search(cr, uid, [("ref", "=", partner.ref), ("multiple_company_rnc", "=", False)]):
                return True
        return False

    _constraints = [
        (osv.osv._check_recursion, 'You cannot create recursive Partner hierarchies.', ['parent_id']),
        (_check_unique_ref,
         u"Esta identificacion ya ha sido registrado! Si quiere utilizar varios relacionados con mismo RNC/Cedula debe indicarlo en el campo --RNC para varias compañias--",
         [u"Rnc/Cédula"]),
    ]

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):

            self.check_access_rights(cr, uid, 'read')
            where_query = self._where_calc(cr, uid, args, context=context)
            self._apply_ir_rules(cr, uid, where_query, 'read', context=context)
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            # TODO: simplify this in trunk with `display_name`, once it is stored
            # Perf note: a CTE expression (WITH ...) seems to have an even higher cost
            #            than this query with duplicated CASE expressions. The bulk of
            #            the cost is the ORDER BY, and it is inevitable if we want
            #            relevant results for the next step, otherwise we'd return
            #            a random selection of `limit` results.
            query = ('''SELECT res_partner.id FROM res_partner
                                  LEFT JOIN res_partner company
                                       ON res_partner.parent_id = company.id'''
                     + where_str + ''' (res_partner.email ''' + operator + ''' %s OR  res_partner.ref ''' + operator + ''' %s OR
                      CASE
                           WHEN company.id IS NULL OR res_partner.is_company
                               THEN res_partner.name
                           ELSE company.name || ', ' || res_partner.name
                      END ''' + operator + ''' %s)
                ORDER BY
                      CASE
                           WHEN company.id IS NULL OR res_partner.is_company
                               THEN res_partner.name
                           ELSE company.name || ', ' || res_partner.name
                      END''')

            where_clause_params += [search_name, search_name]
            where_clause_params.append(search_name)
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)

            cr.execute(query, where_clause_params)
            ids = map(lambda x: x[0], cr.fetchall())

            if ids:
                return self.name_get(cr, uid, ids, context)
            else:
                return []
        return super(res_partner, self).name_search(cr, uid, name, args, operator=operator, context=context,
                                                    limit=limit)

    def get_rnc(self, ref):
        res = requests.get('http://api.marcos.do/rnc/%s' % ref)
        if res.status_code == 200:
            return res.json()
        else:
            return False

    def is_fiscal_id(self, vals):
        value = vals.get("ref", False) or vals.get("name", False)

        if value and (len(value) == 9 or len(value) == 11):
            if value.isdigit():
                return value

        return False

    def create(self, cr, uid, vals, context=None):

        if vals.get("fiscal_position", False):
            fiscal_id = self.pool.get("account.fiscal.position").search(cr, uid, [("fiscal_type", "=", vals["fiscal_position"])])
            if fiscal_id:
                vals.update({"property_account_position": fiscal_id[0]})

        validation = {}

        fiscal_id = self.is_fiscal_id(vals)
        if fiscal_id:
            validation = self.validate_fiscal_id(fiscal_id, context=context)

        if validation:
            if vals.get("property_account_position", False):
                validation.update({"property_account_position": vals["property_account_position"]})
            vals.update(validation)


        try:
            name_is_numeric = vals["name"].isnumeric()
        except:
            name_is_numeric = unicode(vals["name"], 'utf-8').isnumeric()


        if name_is_numeric:
            raise exceptions.ValidationError(u"El número de cédula o rnc no es valido!")
        return super(res_partner, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        partner = self.browse(cr, uid, ids)

        if vals.get("fiscal_position", False):
            fiscal_id = self.pool.get("account.fiscal.position").search(cr, uid, [("fiscal_type", "=", vals["fiscal_position"])])
            if fiscal_id:
                vals.update({"property_account_position": fiscal_id[0]})

        validation = {}
        fiscal_id = self.is_fiscal_id(vals)

        if fiscal_id:
            if vals.get("ref", False):
                validation = self.validate_fiscal_id(u"{}".format(vals["ref"]), context=context)
            elif vals.get("name", False):
                validation = self.validate_fiscal_id(u"{}".format(vals["name"]), context=context)

        if validation:
            if vals.get("property_account_position", False):
                validation.update({"property_account_position": vals["property_account_position"]})
            vals.update(validation)

        return super(res_partner, self).write(cr, uid, ids, vals, context=context)

    def validate_fiscal_id(self, name, context=None):
        vals = {}
        context = context or {}
        supplier = customer = False

        if context.get('search_default_supplier', False):
            supplier = True
        else:
            customer = True
        if name and not len(name) in [9, 11] and name.isnumeric():
            raise osv.except_osv(u"Debe colocar un numero de RNC/Cedula valido!", u"RNC/Cedula")

        if name.isdigit() and len(name) in [9, 11]:
            if _internet_on():
                data = self.get_rnc(name)
                if data:
                    vals['ref'] = data['rnc'].strip()
                    vals['name'] = data['name'].strip()
                    vals["comment"] = u"Nombre Comercial: %s, regimen de pago: %s,  estatus: %s, categoria: %s" % (
                        data['comercial_name'], data['payment_regimen'], data['status'], data['category'])
                    vals['is_company'] = True

                    if customer:
                        vals['property_account_position'] = 1
                    elif supplier:
                        vals["property_account_position"] = 13
            else:
                vals['ref'] = name.strip()
                vals['is_company'] = True

        return vals

    @api.model
    def name_create(self, name):
        vals = self.validate_fiscal_id(name, context=self._context)
        if self._rec_name:
            if vals:
                record = self.create(vals)
                return record.name_get()[0]
            else:
                raise exceptions.ValidationError("A session's instructor can't be an attendee")
        else:
            return super(res_partner, self).name_create(name)