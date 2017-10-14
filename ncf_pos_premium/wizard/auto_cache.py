# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################


from odoo import fields, models, api, _, registry

import logging
import os
import time
import json
import xlsxwriter
import xlrd
import itertools
import glob
import shutil
from odoo.addons.queue_job.job import job
import redis


_logger = logging.getLogger(__name__)
models_need_get = {
    'res.partner': [('customer', '=', True)],
    'product.product': [('sale_ok', '=', True), ('available_in_pos', '=', True)],
}

table_load = ['res_partner', 'product_product']


class pos_auto_cache(models.TransientModel):
    _name = "pos.auto.cache"

    @api.model
    def get_data(self):
        _logger.info('start loading get_data()')
        start_time = time.time()

        use_redis, redis_db_pos = self.get_config()

        if use_redis:
            datas = {"res_partner": [], "product_product": []}
            redis_ids = redis_db_pos.scan_iter()
            for redis_id in redis_ids:
                table, id = redis_id.split(":")
                datas[table].append(json.loads(redis_db_pos.get(redis_id)))
        else:
            for table in table_load:
                datas[table] = []

                if not use_redis:
                    data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '../datas', self._cr.dbname))
                    file_dir_extension = os.path.join(data_dir, '*' + table + '_*copy*')
                    for path_file in glob.glob(file_dir_extension):
                        book = xlrd.open_workbook(path_file)
                        sheet = book.sheet_by_index(0)
                        for row in itertools.imap(sheet.row, range(sheet.nrows)):
                            for cell in row:
                                datas[table].append(json.loads(cell.value))
                else:
                    if table == "res_partner":
                        for key in partner_redis_db.scan_iter():
                            datas[table].append(json.loads(partner_redis_db.get(key)))
                    else:
                        for key in product_redis_db.scan_iter():
                            datas[table].append(json.loads(product_redis_db.get(key)))

        _logger.info('===: LOADING CACHE POS DATA ====:  %s' % (time.time() - start_time))
        return datas

    def get_data_path(self, filename):
        if not os.path.exists(os.path.realpath(os.path.join(os.path.dirname(__file__), '../datas', self._cr.dbname))):
            os.makedirs(os.path.realpath(os.path.join(os.path.dirname(__file__), '../datas', self._cr.dbname)))
        path = os.path.realpath(os.path.join(os.path.dirname(__file__), '../datas', self._cr.dbname))
        return os.path.join(path, filename)

    def get_config(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        redis_db_pos_cache = config_parameter.get_param("redis_db_pos_cache")
        redis_db_pos = False

        if redis_db_pos_cache == "False":
            use_redis = False
        else:
            use_redis = True
            redis_db_pos = redis.StrictRedis(host='localhost', port=6379, db=int(redis_db_pos_cache))


        return use_redis, redis_db_pos


    @api.multi
    @job
    def _auto_cache_data(self, table, ids, sigle_cache=False):
        """

        :param table:
        :param ids:
        :param sigle_cache True if callback from sigle record:
        :return:
        """
        use_redis, redis_db_pos = self.get_config()

        if use_redis and sigle_cache:
            for id in ids:
                redis_db_pos.delete("{}:{}".format(table, id))

        _logger.info('query %s with start ID %s and End ID %s' % (table, min(ids), max(ids)))
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            start_time = time.time()
            model = table.split('_')
            module_name = ''

            for i in model:
                if not module_name:
                    module_name += i
                else:
                    module_name += '.' + i
            model_fields = self.env[module_name].fields_get()
            fields_load = []
            fields_orm = []

            for k, v in model_fields.iteritems():
                if v['type'] in ['many2many', 'many2one'] and v['store'] == True:
                    fields_orm.append(k)
                if v['type'] not in ['one2many', 'binary', 'monetary', 'many2many'] and v['store'] == True:
                    fields_load.append(k)

            if table != 'product_product':

                sql_select = "SELECT id "

                for i in fields_load:
                    sql_select += ', {}'.format(i)

                sql_from = "FROM {} ".format(table)

                if len(ids) == 1:
                    sql_where = "WHERE id = {}".format(ids[0])
                else:
                    sql_where = "WHERE id in {}".format(tuple(ids))

                sql_query = "{} {} {}".format(sql_select, sql_from, sql_where)

                if table == 'res_partner':
                    sql_query + " AND customer is True AND active is True"

                self.env.cr.execute(sql_query)

                records = self.env.cr.dictfetchall()

                if not use_redis:
                    path_file = self.get_data_path(table + '_' + str(max(ids)) + '.xlsx')

                    workbook = xlsxwriter.Workbook(path_file)

                    worksheet = workbook.add_worksheet()

                    row = 0

                for record in records:
                    sub_records = self.env[module_name].browse(record['id']).read(fields_orm)
                    if sub_records:

                        record.update(sub_records[0])
                        if not use_redis:
                            worksheet.write(row, 0, json.dumps(record))
                            row += 1
                        else:
                            redis_db_pos.set("{}:{}".format(table, record['id']), json.dumps(record))
                    else:
                        _logger.error('Record not found: %s' % record['id'])
                        if not use_redis:
                            records.remove(record)
                if not use_redis:
                    workbook.close()

                    src_file = path_file

                    dst_file = self.get_data_path(table + '_' + str(max(ids)) + '_copy' + '.xlsx')

                    shutil.copy(src_file, dst_file)

                _logger.info(
                    'stored : %s total %s rows,  need a times %s' % (
                        module_name, len(records), (time.time() - start_time)))

            if table == 'product_product':

                price_lists = self.env['product.pricelist'].search([])

                sql_select = "SELECT p.id "

                for i in fields_load:
                    sql_select += ', p.{}'.format(i)

                model_fields = self.env['product.template'].fields_get()

                fields_load = []

                for k, v in model_fields.iteritems():
                    if k != 'id':
                        if v['type'] in ['many2many', 'many2one'] and v['store'] == True:
                            fields_orm.append(k)
                        if v['type'] not in ['one2many', 'binary', 'monetary', 'many2many'] and v['store'] == True:
                            fields_load.append(k)

                for i in fields_load:
                    sql_select += ', pt.{}'.format(i)


                sql_from = " FROM product_product AS p, product_template AS pt "

                sql_where = " WHERE p.product_tmpl_id = pt.id AND pt.sale_ok is True AND pt.available_in_pos is True AND pt.active is True "

                if len(ids) == 1:
                    sql_where += " AND p.id = {}".format(ids[0])
                else:
                    sql_where += " AND p.id in {}".format(tuple(ids))

                sql_query = sql_select + sql_from + sql_where

                _logger.info(sql_query)
                self.env.cr.execute(sql_query)

                records = self.env.cr.dictfetchall()

                if not use_redis:

                    path_file = self.get_data_path(table + '_' + str(max(ids)) + '.xlsx')

                    workbook = xlsxwriter.Workbook(path_file)

                    worksheet = workbook.add_worksheet()

                    row = 0

                for record in records:
                    product = self.env[module_name].browse(record['id'])
                    sub_records = product.read(fields_orm)
                    if sub_records:
                        sub_records[0]['price_with_pricelist'] = {}
                        sub_records[0].update({"qty_available": product.qty_available})
                        for price_list in price_lists:
                            product_with_context = self.env[module_name].browse(record['id']).with_context(
                                pricelist=price_list.id, quantity=1, date_order=fields.Datetime.now())
                            price = product_with_context.price
                            sub_records[0]['price_with_pricelist'][price_list.id] = price
                        record.update(sub_records[0])
                        record['display_name'] = record['name']
                        record['price'] = record['list_price']
                        if not use_redis:
                            worksheet.write(row, 0, json.dumps(record))
                            row += 1
                        else:
                            redis_db_pos.set("{}:{}".format(table, record['id']), json.dumps(record))

                    else:
                        _logger.error('Record not found: %s' % record['id'])
                        if not use_redis:
                            records.remove(record)

                if not use_redis:
                    workbook.close()

                    src_file = path_file

                    dst_file = self.get_data_path(table + '_' + str(max(ids)) + '_copy' + '.xlsx')

                    shutil.copy(src_file, dst_file)

                _logger.info(
                    'stored : {} total {} rows,  need a times {}'.format(module_name, len(records), (time.time() - start_time)))

            self._cr.close()
            return {}

    @api.multi
    def auto_cache(self, type):
        """

        :param type:
         0 run send cron to queue_job
         1 run normal cron
        :return:
        """
        use_redis, redis_db_pos = self.get_config()
        partner_ids = []
        product_ids = []
        if use_redis:
            redis_ids = redis_db_pos.scan_iter()
            for redis_id in redis_ids:
                table, id = redis_id.split(":")
                if table == "res_partner":
                    partner_ids.append(id)
                elif table == "product_product":
                    product_ids.append(id)

        _logger.info('===> BEGIN auto_cache')
        for table in table_load:

            self.env.cr.execute("SELECT id FROM {} WHERE active is TRUE".format(table))
            records = self.env.cr.dictfetchall()

            ids = [record["id"] for record in records]

            if table == "res_partner":
                for partner_id in  product_ids:
                    if int(partner_id) not in ids:
                        redis_db_pos.delete("{}:{}".format(table,partner_id))
            elif table == "product_product":
                for product_id in  product_ids:
                    if int(product_id) not in ids:
                        redis_db_pos.delete("{}:{}".format(table,product_id))

            total_records = len(ids)

            if total_records > 10000:
                chunks = [ids[x:x + 10000] for x in xrange(0, len(ids), 10000)]

                for chunk in chunks:
                    if type == 0:
                        self.with_delay(channel="root.poscache")._auto_cache_data(table, tuple(chunk))
                    else:
                        self._auto_cache_data(table, tuple(chunk))
            else:
                if type == 0:
                    self.with_delay(channel="root.poscache")._auto_cache_data(table, tuple(ids))
                else:
                    self._auto_cache_data(table, tuple(ids))
        _logger.info('===> END auto_cache')
        return 1
