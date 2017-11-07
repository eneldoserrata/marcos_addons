# -*- coding: utf-8 -*-
from odoo import api, models, fields
import logging
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class product_template(models.Model):
    _inherit = "product.template"

    not_returnable = fields.Boolean('No retornable')

    @api.multi
    def write(self, vals):
        res = super(product_template, self).write(vals)
        notifications = []
        product_fields = self.env['product.product'].fields_get()
        product_fields_load = []
        for k, v in product_fields.iteritems():
            if v['type'] not in ['one2many', 'binary', 'monetary']:
                product_fields_load.append(k)

        for product in self:
            products = self.env['product.product'].search([('product_tmpl_id', '=', product.id)])
            products.pos_cache_update(products.ids)
            for p in products:
                if p and p.sale_ok and p.available_in_pos:
                    product_datas = p.sudo().read(product_fields_load)[0]
                    product_datas['price'] = product_datas['list_price']
                    product_datas['model'] = 'product.product'
                    notifications.append(("pos.sync.backend",product_datas))
        if not self._context.get("job_uuid", False):
            if notifications:
                _logger.info('===> sending')
                pos_configs = self.env["pos.config"].search([('multi_session_id','!=',False)])
                if pos_configs and notifications:
                    pos_configs._send_to_channel("pos.sync.backend", notifications)
        return res


class product_product(models.Model):
    _inherit = 'product.product'

    @api.multi
    def pos_cache_update(self, product_ids):
        if product_ids:
            if not self._context.get("job_uuid", False):
                pos_cache = self.env["pos.auto.cache"]
                use_redis, redis_db_pos = pos_cache.get_config()
                if use_redis:
                    pos_cache.with_delay(description="update product cache", channel="root.poscache")._auto_cache_data("product_product", product_ids,
                                                                               sigle_cache=True)

    @api.multi
    def remove_from_cache(self):
        if not self._context.get("job_uuid", False):
            pos_cache = self.env["pos.auto.cache"]
            use_redis, redis_db_pos = pos_cache.get_config()
            if use_redis:
                for id in self.ids:
                    redis_db_pos.delete("{}:{}".format("product.product", id))


    @api.model
    def create(self, vals):
        product = super(product_product, self).create(vals)
        notifications = []
        if product.sale_ok and product.available_in_pos:
            product_fields = self.env['product.product'].fields_get()
            product_fields_load = []
            for k, v in product_fields.iteritems():
                if v['type'] not in ['one2many', 'binary', 'monetary']:
                    product_fields_load.append(k)
            product_datas = product.sudo().read(product_fields_load)[0]
            product_datas['price'] = product_datas['list_price']
            product_datas['model'] = 'product.product'
            notifications.append(("pos.sync.backend", product_datas))
        if not self._context.get("job_uuid", False):
            if notifications:
                _logger.info('===> sending')
                pos_configs = self.env["pos.config"].search([('multi_session_id','!=',False)])
                if pos_configs and notifications:
                    pos_configs._send_to_channel("pos.sync.backend", notifications)
            self.pos_cache_update(product.ids)
        return product
