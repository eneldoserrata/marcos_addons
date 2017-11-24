odoo.define('ncf_pos_premium.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var Model = require('web.DataModel');
    var bus = require('bus.bus');
    var session = require('web.session');
    var Keypad = require('ncf_pos_premium.keyboard');

    var exports = require('ncf_pos_premium.pos_longpolling');

    models.load_fields('res.users', ['allow_payments', 'allow_add_order', 'allow_delete_order', 'allow_discount', 'allow_edit_price', 'allow_decrease_amount', 'allow_delete_order_line', 'allow_create_order_line', 'allow_refund_order']);

    models.load_fields('product.product', ['not_returnable', 'qty_available']);

    models.load_fields('res.partner', ['sale_fiscal_type']);

    models.load_fields('account.journal', ['credit']);

    models.load_fields('pos.config', ['default_partner_id']);

    models.load_models([{
        model: 'account.bank.statement.line',
        fields: ['id', 'journal_id', 'amount'],
        loaded: function (self, statements) {
            self.db.all_statements = statements;
            self.db.statement_by_id = {};
            statements.forEach(function (statement) {
                self.db.statement_by_id[statement.id] = statement;
            });
        }
    }]);

    models.load_models([{
        model: 'qty.pos.fraction',
        fields: ['id', 'name', 'qty'],
        loaded: function (self, fractions) {
            self.set("fractions", fractions)
        }
    }]);

    models.load_models({
        model: 'pos.order',
        fields: ['id', 'name', 'date_order', 'partner_id', 'partner_id.email', 'lines', 'pos_reference', 'invoice_id', 'is_return_order', 'return_order_id', 'return_status', 'statement_ids', 'amount_total', 'order_priority'],
        domain: function (self) {
            var domain_list = [];
            if (self.config.order_loading_options == 'n_days') {
                var today = new Date();
                var validation_date = new Date(today.setDate(today.getDate() - self.config.number_of_days)).toISOString();
                domain_list = [['date_order', '>', validation_date], ['state', 'not in', ['draft', 'cancel']]]
            }
            else
                domain_list = [['session_id', '=', self.pos_session.name], ['state', 'not in', ['draft', 'cancel']]]
            return domain_list;
        },
        loaded: function (self, wk_order) {
            self.db.pos_all_orders = wk_order;
            self.db.order_by_id = {};
            wk_order.forEach(function (order) {
                self.db.order_by_id[order.id] = order;
            });

            self.sale_fiscal_type = [{"code": "final", "name": "Final"},
                {"code": "fiscal", "name": "Fiscal"},
                {"code": "gov", "name": "Gubernamental"},
                {"code": "special", "name": "Especiales"}];

            var vitual_journal = {
                credit: true,
                ipf_payment_type: "credit_note",
                type: "cash",
                id: 1000000,
                sequence: 1000000
            };
            self.journals.push(vitual_journal);

            var virtual_pos_journal_for_credit_payment = {
                user_id: [self.get_cashier().id, self.get_cashier().name],
                name: self.pos_session.name,
                pos_session_id: [self.pos_session.id, self.pos_session.name],
                journal_id: [1000000, "NOTA DE CRÉDITO"],
                currency_id: [74, "DOP"],
                state: "open",
                id: 1000000,
                account_id: [1000000, "Virtual pos account_id for credit note"],
                payment_reference: "",
                journal: vitual_journal
            };
            self.cashregisters.push(virtual_pos_journal_for_credit_payment);
            self.cashregisters_by_id[1000000] = virtual_pos_journal_for_credit_payment;
        }
    });

    models.load_models({
        model: 'pos.order.line',
        fields: ['product_id', 'order_id', 'qty', 'discount', 'price_unit', 'price_tax', 'price_subtotal_incl', 'price_subtotal', 'line_qty_returned'],
        domain: function (self) {
            var order_lines = []
            var orders = self.db.pos_all_orders;
            for (var i = 0; i < orders.length; i++) {
                order_lines = order_lines.concat(orders[i]['lines']);
            }
            return [
                ['id', 'in', order_lines]
            ];
        },
        loaded: function (self, wk_order_lines) {
            self.db.pos_all_order_lines = wk_order_lines;
            self.db.line_by_id = {};
            wk_order_lines.forEach(function (line) {
                self.db.line_by_id[line.id] = line;
            });
        },
    });

    bus.bus.activated = true; // fake value to ignore start_polling call

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        // pos_multi_session | pos_multi_session_restaurant | pos_longpolling
        initialize: function (session, attributes) {
            var self = this;
            this.keypad = new Keypad.Keypad({'pos': this});
            _super_posmodel.initialize.apply(this, arguments);
            if (!this.message_ID) {
                this.message_ID = 1;
            }
            this.channels = {};
            this.lonpolling_activated = false;
            this.bus = bus.bus;
            this.longpolling_connection = new exports.LongpollingConnection(this);

            var channel_name = "pos.longpolling";
            var callback = this.longpolling_connection.network_is_on;
            this.add_channel(channel_name, callback, this.longpolling_connection);

            this.ready.then(function () {
                self.start_longpolling();
            });

            this.multi_session = false;
            this.ms_syncing_in_progress = false;
            this.get('orders').bind('remove', function (order, collection, options) {
                if (!self.multi_session.client_online) {
                    if (order.order_on_server) {
                        self.multi_session.no_connection_warning();
                        if (self.debug) {
                            console.log('PosModel initialize error');
                        }
                        return false;
                    }
                }
                order.ms_remove_order();
            });

            this.multi_session = new exports.MultiSession(this);
            var channel_name = "pos.multi_session";
            var callback = this.ms_on_update;
            this.add_channel(channel_name, callback, this);

            var channel_name = "pos.sync.backend";
            var callback = this.sync_backend_on_notification_do;
            this.add_channel(channel_name, callback, this);

            this.multi_session.remove_order = function (data) {
                if (data.transfer) {
                    data.transfer = false;
                    return;
                } else {
                    this.send({action: 'remove_order', data: data});
                }
            };

        },
        sync_backend_on_notification_do: function (message, sync_all) {

            if (Array.isArray(message)) {
                for (var i = 0; i < message.length; i++) {
                    var message = message[i][1];
                    if (message.model == 'product.product') {
                        this.update_product(message)
                    }
                    else if (message.model == 'res.partner') {
                        this.update_partner(message)
                    } else if (message.model == 'stock.inventory.line') {
                        this.sync_product_qty(message)
                    }

                }
            }
        },
        sync_product_qty: function (message) {
            var product = this.db.get_product_by_id(message.id);
            if (product) {
                product.qty_available = message.qty;
                var $elem = $("[data-product-id='" + message.id + "'] .qty-tag");
                $elem.html(message.qty);
            }
        },
        update_product: function (product_data) {
            this.db.add_products([product_data]);
            var $elem = $("[data-product-id='" + product_data.id + "'] .price-tag");
            var str = '$ ' + product_data['list_price'];
            if (product_data['uom_id']) {
                str += '/' + product_data['uom_id'][1]
            }
            $elem.html(str);
            var $elem = $("[data-product-id='" + product_data.id + "'] .product-name");
            $elem.html(product_data['name']);
        },
        update_partner: function (customer_data) {

            var partner_exsit = _.filter(this.partners, function (partner) {
                return partner.id == customer_data.id;
            });
            if (!partner_exsit.length) {
                this.partners.push(customer_data)
                this.db.add_partners([customer_data])
            } else {
                partner_exsit = customer_data;
                this.db.add_partners([customer_data])
            }
        },
        //pos_multi_session_restaurant
        add_new_order: function () {
            var res = _super_posmodel.add_new_order.apply(this, arguments);
            if (this.multi_session) {
                var current_order = this.get_order();
                if (current_order != null) {
                    current_order.ms_update();
                }
            }
            return res
        },
        // pos_multi_session | pos_multi_session_restaurant
        ms_on_update: function (message, sync_all) {

            var self = this;
            var data = message.data || {};
            var order = false;
            var old_order = this.get_order();


            if (data.uid) {
                order = this.get('orders').find(function (order) {
                    return order.uid == data.uid;
                });
            }


            if (order != undefined) {
                if (order.floor_id != undefined) {
                    if (order && order.table == null) {
                        order.transfer = true;
                        order.destroy({'reason': 'abandon'});
                    } else if (order && order.table.id != data.table_id) {
                        order.transfer = true;
                        order.destroy({'reason': 'abandon'});
                    }
                }
            }
            self.ms_on_update_pos_multi_session(message, sync_all);

            if ((order && old_order && old_order.uid != order.uid) || (old_order == null)) {
                this.set('selectedOrder', old_order);
            }

            if (self.config.pos_kitchen_view) {
                self.gui.show_screen('kitchen_screen');
                self.gui.screen_instances.kitchen_screen.renderElement();
            }
        },
        ms_on_update_pos_multi_session: function (message, sync_all) {
            this.ms_syncing_in_progress = true; // don't broadcast updates made from this message
            var error = false;
            var self = this;
            var data = '';
            var action = '';
            try {
                if (this.debug) {
                    console.log('MS', this.config.name, 'on_update:', JSON.stringify(message));
                }
                action = message.action;
                data = message.data || {};
                var order = false;
                if (data.uid) {
                    order = this.get('orders').find(function (order) {
                        return order.uid == data.uid;
                    });
                }
                if (sync_all) {
                    this.message_ID = data.message_ID;
                    this.ms_do_update(order, data);
                } else {
                    if (self.message_ID + 1 != data.message_ID)
                        self.multi_session.request_sync_all();
                    else
                        self.message_ID = data.message_ID;
                    if (order && action == 'remove_order') {
                        order.destroy({'reason': 'abandon'});
                    }
                    else if (action == 'update_order') {
                        this.ms_do_update(order, data);
                    }
                }
            } catch (err) {
                error = err;
                //console.error(err);
            }
            this.ms_syncing_in_progress = false;
            if (error) {
                throw(error);
            }

        },
        start_longpolling: function () {
            var self = this;
            this.bus.last = this.db.load('bus_last', 0);
            this.bus.on("notification", this, this.on_notification);
            this.bus.stop_polling();
            _.each(self.channels, function (value, key) {
                self.init_channel(key);
            });
            this.bus.start_polling();
            this.lonpolling_activated = true;
            this.longpolling_connection.send();
        },
        add_channel: function (channel_name, callback, thisArg) {

            if (thisArg) {
                callback = _.bind(callback, thisArg);
            }
            this.channels[channel_name] = callback;
            if (this.lonpolling_activated) {
                this.init_channel(channel_name);
            }
        },
        get_full_channel_name: function (channel_name) {
            return JSON.stringify([session.db, channel_name, String(this.config.id)]);
        },
        init_channel: function (channel_name) {
            var channel = this.get_full_channel_name(channel_name);
            this.bus.add_channel(channel);
        },
        remove_channel: function (channel_name) {
            if (channel_name in this.channels) {
                delete this.channels[channel_name];
                var channel = this.get_full_channel_name(channel_name);
                this.bus.delete_channel(channel);
            }
        },
        on_notification: function (notification) {
            for (var i = 0; i < notification.length; i++) {
                var channel = notification[i][0];
                var message = notification[i][1];
                this.on_notification_do(channel, message);
            }
            this.db.save('bus_last', this.bus.last);
        },
        on_notification_do: function (channel, message) {
            var self = this;
            if (_.isString(channel)) {
                var channel = JSON.parse(channel);
            }

            if (Array.isArray(channel) && (channel[1] in self.channels)) {
                try {
                    self.longpolling_connection.network_is_on();

                    var callback = self.channels[channel[1]];
                    if (callback) {

                        // if (self.debug) {
                        //     console.log('POS LONGPOLLING', self.config.name, channel[1], JSON.stringify(message));
                        // }
                        callback(message);
                    }
                } catch (err) {
                    this.chrome.gui.show_popup('error', {
                        'title': 'Error',
                        'body': err,
                    });
                }
            }
        },
        ms_my_info: function () {
            var user = this.cashier || this.user;
            return {
                'user': {
                    'id': user.id,
                    'name': user.name,
                },
                'pos': {
                    'id': this.config.id,
                    'name': this.config.name,
                }
            };
        },
        // pos_multi_session | pos_multi_session_restaurant
        on_removed_order: function (removed_order, index, reason) {
            if (this.multi_session) {
                if (reason === 'finishOrder') {
                    if (this.get('orders').size() > 0) {
                        return this.set({'selectedOrder': this.get('orders').at(index) || this.get('orders').first()});
                    }
                    this.add_new_order();
                    this.get('selectedOrder').ms_replace_empty_order = true;
                    return;
                } else if (this.ms_syncing_in_progress) {
                    if (this.get('orders').size() === 0) {
                        this.add_new_order();
                    } else {
                        return this.set({'selectedOrder': this.get('orders').at(index) || this.get('orders').first()});
                    }
                    return;
                }
            }
            var res = _super_posmodel.on_removed_order.apply(this, arguments);
            this.trigger('change:orders-count-on-floor-screen');
            return res

        },
        // pos_multi_session | pos_multi_session_restaurant
        ms_on_add_order: function (current_order) {
            if (!current_order) {
                this.trigger('change:orders-count-on-floor-screen');

            } else {

                if (!current_order) {
                    return;
                }
                var is_frozen = !current_order.ms_replace_empty_order;

                if (this.config.multi_session_replace_empty_order && current_order.new_order && !is_frozen) {
                    current_order.destroy({'reason': 'abandon'});
                } else if (is_frozen || !current_order.new_order || !this.config.multi_session_deactivate_empty_order) {
                    // keep current_order active
                    this.set('selectedOrder', current_order);
                }
            }


        },
        // pos_multi_session | pos_multi_session_restaurant
        ms_create_order: function (options) {
            var self = this;
            options = _.extend({pos: this}, options || {});
            var order = new models.Order({}, options);

            if (order) {
                if (options.data.table_id) {
                    order.table = self.tables_by_id[options.data.table_id];
                    order.customer_count = options.data.customer_count;
                    order.save_to_db();
                }
                return order;
            }
        },
        // pos_multi_session | pos_multi_session_restaurant
        ms_do_update: function (order, data) {
            var self = this;
            var pos = this;
            this.pos_session.order_ID = data.sequence_number;
            if (!order) {
                var create_new_order = pos.config.multi_session_accept_incoming_orders || !(data.ms_info && data.ms_info.created.user.id != pos.ms_my_info().user.id);
                if (!create_new_order) {
                    return;
                }
                var json = {
                    sequence_number: data.sequence_number,
                    order_priority: data.order_priority,
                    uid: data.uid,
                    pos_session_id: this.pos_session.id,
                    statement_ids: false,
                    lines: false,
                    multiprint_resume: data.multiprint_resume,
                    new_order: false,
                    order_on_server: true,
                };
                order = this.ms_create_order({
                    ms_info: data.ms_info,
                    revision_ID: data.revision_ID,
                    data: data,
                    json: json
                });
                var current_order = this.get_order();
                this.get('orders').add(order);
                this.ms_on_add_order(current_order);
            } else {
                order.ms_info = data.ms_info;
                order.revision_ID = data.revision_ID;
                order.sequence_number = data.sequence_number;
                order.order_priority = data.order_priority;
            }
            var not_found = order.orderlines.map(function (r) {
                return r.uid;
            });
            if (data.partner_id !== false) {
                var client = order.pos.db.get_partner_by_id(data.partner_id);
                if (!client) {

                    $.when(this.load_new_partners_by_id(data.partner_id))
                        .then(function (client) {
                            client = order.pos.db.get_partner_by_id(data.partner_id);
                            order.set_client(client);
                        }, function () {
                        });
                }
                order.set_client(client);
            }
            else {
                order.set_client(null);
            }
            _.each(data.lines, function (dline) {
                dline = dline[2];
                var line = order.orderlines.find(function (r) {
                    return dline.uid == r.uid;
                });
                not_found = _.without(not_found, dline.uid);
                var product = pos.db.get_product_by_id(dline.product_id);
                if (!line) {
                    line = new models.Orderline({}, {pos: pos, order: order, product: product});
                    line.uid = dline.uid;
                }
                line.ms_info = dline.ms_info || {};
                if (dline.qty !== undefined) {
                    line.set_quantity(dline.qty);
                }
                if (dline.price_unit !== undefined) {
                    line.set_unit_price(dline.price_unit);
                }
                if (dline.discount !== undefined) {
                    line.set_discount(dline.discount);
                }
                if (dline.mp_dirty !== undefined) {
                    line.set_dirty(dline.mp_dirty);
                }
                if (dline.mp_skip !== undefined) {
                    line.set_skip(dline.mp_skip);
                }
                if (dline.note !== undefined) {
                    line.set_note(dline.note);
                }
                order.orderlines.add(line);
            });

            _.each(not_found, function (uid) {
                var line = order.orderlines.find(function (r) {
                    return uid == r.uid;
                });
                order.orderlines.remove(line);
            });
            order.order_on_server = true;
            order.new_order = false;

            if (this.gui.screen_instances.products.action_buttons.guests != undefined) {
                if (order) {
                    order.set_customer_count(data.customer_count, true);
                    order.saved_resume = data.multiprint_resume;
                    order.trigger('change');
                    this.gui.screen_instances.floors.renderElement();
                }
            }
        },
        load_new_partners_by_id: function (partner_id) {
            var self = this;
            var def = new $.Deferred();
            var client;
            var fields = _.find(this.models, function (model) {
                return model.model === 'res.partner';
            }).fields;
            new Model('res.partner')
                .query(fields)
                .filter([['id', '=', partner_id]])
                .all({'timeout': 3000, 'shadow': true})
                .then(function (partners) {
                    if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                        def.resolve();
                    } else {
                        def.reject();
                    }
                }, function (err, event) {
                    event.preventDefault();
                    def.reject();
                });
            return def;
        },
        load_server_data: function () {
            var self = this;

            self.model_blocked_loading = [
                'product.product',
                'res.partner'
            ];

            for (var i in self.model_blocked_loading) {
                if (self.model_blocked_loading[i] == 'res.partner') {
                    var partner_index = _.findIndex(self.models, function (model) {
                        return model.model == self.model_blocked_loading[i];
                    });
                    self.partner_model = this.models[partner_index];
                    if (partner_index !== -1) {
                        self.models.splice(partner_index, 1);
                    }
                } else {
                    var model_index = _.findIndex(self.models, function (model) {
                        return model.model == self.model_blocked_loading[i];
                    });

                    if (model_index !== -1) {
                        self.models.splice(model_index, 1);
                    }
                }
            }


            return _super_posmodel.load_server_data.apply(this, arguments).then(function () {
                return new Model('pos.auto.cache').call('get_data', []).then(function (json_data) {
                    var partners_json = json_data['res_partner'];
                    var products_json = json_data['product_product'];
                    if (self.pricelist && self.pricelist.id) {
                        for (var i = 0; i < products_json.length; i++) {
                            if (products_json[i].price_with_pricelist) {
                                var public_price = products_json[i]['price_with_pricelist'][self.pricelist.id];
                                products_json[i]['price'] = public_price;
                                products_json[i]['list_price'] = public_price;
                            }

                        }
                    }
                    self.db.add_products(products_json);
                    self.partners = partners_json;
                    self.db.add_partners(partners_json);
                    self.models.push(self.partner_model);
                });
            })
        },
        set_cashier: function () {
            _super_posmodel.set_cashier.apply(this, arguments);
            this.trigger('change:cashier', this);
        },
        push_and_invoice_order: function (order) {

            var self = this;
            var invoiced = new $.Deferred();
            if (!order.get_client()) {
                invoiced.reject({code: 400, message: 'Missing Customer', data: {}});
                return invoiced;
            }
            var order_id = this.db.add_order(order.export_as_JSON());
            this.flush_mutex.exec(function () {
                var done = new $.Deferred();
                var transfer = self._flush_orders([self.db.get_order(order_id)], {timeout: 30000, to_invoice: true});
                transfer.fail(function (error) {
                    invoiced.reject(error);
                    done.reject();
                });
                transfer.pipe(function (order_server_id) {
                    self.chrome.do_action('point_of_sale.pos_invoice_report', {
                        additional_context: {
                            //Code chenged for POS All Orders List --START--
                            active_ids: [order_server_id.orders[0].id],
                            // Code chenged for POS All Orders List --END--
                        }
                    });
                    invoiced.resolve();
                    done.resolve();
                });
                return done;
            });
            return invoiced;
        },
        _save_to_server: function (orders, options) {

            var self = this;

            options.timeout = 100000;
            return _super_posmodel._save_to_server.call(this, orders, options).then(function (return_dict) {
                if (return_dict.orders != null) {
                    return_dict.orders.forEach(function (order) {
                        if (order.existing) {
                            self.db.pos_all_orders.forEach(function (order_from_list) {
                                if (order_from_list.id == order.original_order_id)
                                    order_from_list.return_status = order.return_status
                            });
                        }
                        else {
                            self.db.pos_all_orders.unshift(order);
                            self.db.order_by_id[order.id] = order;
                        }
                    });
                    return_dict.orderlines.forEach(function (orderline) {
                        if (orderline.existing) {
                            var target_line = self.db.line_by_id[orderline.id];
                            target_line.line_qty_returned = orderline.line_qty_returned;
                        }
                        else {
                            self.db.pos_all_order_lines.unshift(orderline);
                            self.db.line_by_id[orderline.id] = orderline;
                        }
                    });
                    if (self.db.all_statements)
                        return_dict.statements.forEach(function (statement) {
                            self.db.all_statements.unshift(statement);
                            self.db.statement_by_id[statement.id] = statement;
                        });

                }
                return return_dict;
                //Code for POS All Orders List --start--
            });
        },
        set_order: function (order) {

            _super_posmodel.set_order.call(this, order);
            if (order) {
                if (!order.is_return_order) {
                    $("#cancel_refund_order").hide();
                }
                else {
                    $("#cancel_refund_order").show();
                }
            }
        },
        // changes the current table.
        // pos_multi_session | pos_multi_session_restaurant
        set_table: function (table) {
            var self = this;
            if (table && this.order_to_transfer_to_different_table) {
                this.order_to_transfer_to_different_table.table = table;
                this.order_to_transfer_to_different_table.ms_update();
                this.order_to_transfer_to_different_table = null;
                // set this table
                this.set_table(table);
            } else {
                _super_posmodel.set_table.apply(this, arguments);
            }
        },
        set_start_order: function () {
            var orders = this.get('orders').models;

            if (orders.length && !this.get('selectedOrder')) {
                this.set('selectedOrder', orders[0]);
            } else {
                this.add_new_order();
            }
        }

    });

    var is_first_order = true;
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            var self = this;
            options = options || {};

            if (!options.json || !('new_order' in options.json)) {
                this.new_order = true;
            }

            _super_order.initialize.apply(this, arguments);

            this.ms_info = {};

            this.revision_ID = options.revision_ID || 1;

            if (!_.isEmpty(options.ms_info)) {
                this.ms_info = options.ms_info;
            } else if (this.pos.multi_session) {
                this.ms_info.created = this.pos.ms_my_info();
            }

            this.ms_replace_empty_order = is_first_order;

            is_first_order = false;

            this.bind('change:sync', function () {
                self.ms_update();
            });

            this.return_status = '-';
            this.is_return_order = false;
            this.return_order_id = false;
            // this.order_priority = 0;

            if (!this.get_client()) {
                var default_partner_id = this.pos.db.get_partner_by_id(this.pos.config.default_partner_id[0]);
                if (default_partner_id) {
                    this.set_client(default_partner_id);
                }
            }

        },
        remove_orderline: function (line) {
            _super_order.remove_orderline.apply(this, arguments);
            line.order.trigger('change:sync');
        },
        add_product: function () {
            this.trigger('change:sync');
            _super_order.add_product.apply(this, arguments);
        },
        set_client: function (client) {
            /*  trigger event before calling add_product,
             because event handler ms_update updates some values of the order (e.g. new_name),
             while add_product saves order to localStorage.
             So, calling add_product first would lead to saving obsolete values to localStorage.
             From the other side, ms_update work asynchronously (via setTimeout) and will get updates from add_product method
             */
            this.trigger('change:sync');
            _super_order.set_client.apply(this, arguments);
            // pos_multi_session
        }, ms_check: function () {
            if (!this.pos.multi_session)
                return;
            if (this.pos.ms_syncing_in_progress)
                return;
            if (this.temporary)
                return;
            return true;
        },
        ms_update: function () {
            var self = this;
            if (this.new_order) {
                this.new_order = false;
                this.pos.pos_session.order_ID = this.pos.pos_session.order_ID + 1;
                this.sequence_number = this.pos.pos_session.order_ID;
                this.trigger('change:update_new_order');
            } else {
                this.trigger('change');
            }
            if (!this.ms_check())
                return;
            if (this.ms_update_timeout)
            // restart timeout
                clearTimeout(this.ms_update_timeout);
            this.ms_update_timeout = setTimeout(
                function () {
                    self.ms_update_timeout = false;
                    self.do_ms_update();
                }, 0);
        },
        // pos_multi_session
        ms_remove_order: function () {
            if (!this.ms_check())
                return;
            this.do_ms_remove_order();
        },
        // pos_multi_session | pos_multi_session_restaurant
        do_ms_remove_order: function () {
            if (this.transfer) {
                this.pos.multi_session.remove_order({
                    'uid': this.uid,
                    'revision_ID': this.revision_ID,
                    'transfer': this.transfer
                });
            } else {
                this.pos.multi_session.remove_order({'uid': this.uid, 'revision_ID': this.revision_ID});
            }

        },
        // pos_multi_session
        export_as_JSON: function () {

            var json = _super_order.export_as_JSON.apply(this, arguments);
            var current_order = this.pos.get_order();
            if (current_order != null) {
                json.is_return_order = this.is_return_order;
                json.return_status = this.return_status;
                json.return_order_id = this.return_order_id;
                json.order_note = this.get_order_note();
                json.order_priority = this.order_priority;
            }
            json.ms_info = this.ms_info;
            json.revision_ID = this.revision_ID;
            json.new_order = this.new_order;
            json.order_on_server = this.order_on_server;
            return json;
        },
        // pos_multi_session
        init_from_JSON: function (json) {
            this.new_order = json.new_order;
            this.order_on_server = json.order_on_server;
            _super_order.init_from_JSON.apply(this, arguments);
        },
        do_ms_update: function () {
            var self = this;
            if (this.enquied)
                return;
            var f = function () {
                self.enquied = false;
                var data = self.export_as_JSON();
                return self.pos.multi_session.update(data).done(function (res) {
                    self.order_on_server = true;
                    if (res && res.action == "update_revision_ID") {
                        var server_revision_ID = res.revision_ID;
                        var order_ID = res.order_ID;
                        if (order_ID && self.sequence_number != order_ID) {
                            self.sequence_number = order_ID;
                            self.order_priority = res.order_priority;
                            // sequence number replace
                            self.pos.pos_session.order_ID = order_ID;
                            // rerender order
                            self.trigger('change');
                        }
                        if (server_revision_ID && server_revision_ID > self.revision_ID) {
                            self.revision_ID = server_revision_ID;
                        }
                    }
                })
            };
            this.enquied = true;
            this.pos.multi_session.enque(f);

        },
        get_order_note: function () {
            return $("#order_note").val();
        },
        set_return_status: function (return_status) {
            this.return_status = return_status;
        },
        set_is_return_order: function (is_return_order) {
            this.is_return_order = is_return_order;
        },
        set_return_order_id: function (return_order_id) {
            this.return_order_id = return_order_id;
        },
        add_paymentline: function (cashregister) {
            this.assert_editable(cashregister);

            var newPaymentline = new models.Paymentline({}, {
                order: this,
                cashregister: cashregister,
                pos: this.pos
            });

            if (cashregister.payment_reference != undefined) {
                newPaymentline.set_payment_reference(cashregister.payment_reference);
            }

            var credit_amount = Math.max(cashregister.credit_amount, 0);
            var due = Math.max(this.get_due(), 0);

            if (cashregister.journal.credit) {

                if (credit_amount < due) {
                    newPaymentline.set_amount(credit_amount);
                } else {
                    newPaymentline.set_amount(due);
                }
            } else {

                if (cashregister.journal.type !== 'cash' || this.pos.config.iface_precompute_cash) {
                    newPaymentline.set_amount(due);
                }

            }
            this.paymentlines.add(newPaymentline);
            this.select_paymentline(newPaymentline);
            this.paymentlines.trigger('change', this);

        },
        // pos_multi_session | pos_multi_session_restaurant
        set_customer_count: function (count, skip_ms_update) {
            _super_order.set_customer_count.apply(this, arguments);
            if (!skip_ms_update) {
                this.ms_update();
            }
        },
        // pos_multi_session | pos_multi_session_restaurant
        printChanges: function () {
            _super_order.printChanges.apply(this, arguments);
            this.just_printed = true;
        },
        generate_unique_id: function () {
            // Generates a public identification number for the order.
            // The generated number must be unique and sequential. They are made 12 digit long
            // to fit into EAN-13 barcodes, should it be needed

            function makeid() {
                var text = "";
                var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

                for (var i = 0; i < 5; i++)
                    text += possible.charAt(Math.floor(Math.random() * possible.length));

                return text;
            }

            function zero_pad(num, size) {
                var s = "" + num;
                while (s.length < size) {
                    s = "0" + s;
                }
                return s;
            }

            var uid = zero_pad(this.pos.pos_session.id, 5) + '-' +
                zero_pad(this.pos.pos_session.login_number, 3) + '-' +
                zero_pad(this.sequence_number, 4) + '-' + makeid();

            return uid
        },
    });

    var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {

            var self = this;
            _super_order_line.initialize.apply(this, arguments);
            this.line_qty_returned = 0;
            this.original_line_id = null;

            if (!this.uid) {
                var uid = this.order.uid + '-' + this.id;
                this.uid = uid;
            }
            this.order_uid = this.order.uid;

            _super_order_line.initialize.apply(this, arguments);
            this.ms_info = {}

            if (!this.order) {
                // probably impossible case in odoo 10.0, but keep it here to remove doubts
                return;
            }

            this.uid = this.order.generate_unique_id() + '-' + this.id;
            if (this.order.screen_data.screen === "splitbill") {
                return;
            }

            if (this.order.ms_check()) {
                this.ms_info.created = this.order.pos.ms_my_info();
            }

            this.bind('change', function (line) {
                if (this.order.just_printed) {
                    line.order.trigger('change:sync');
                    return;
                }
                if (self.order.ms_check() && !line.ms_changing_selected) {
                    line.ms_info.changed = line.order.pos.ms_my_info();
                    line.order.ms_info.changed = line.order.pos.ms_my_info();
                    var order_lines = line.order.orderlines;
                    order_lines.trigger('change', order_lines); // to rerender line
                    line.order.trigger('change:sync');
                }
            });
            this.order_line_status = 0;

        },
        set_selected: function () {
            this.ms_changing_selected = true;
            _super_order_line.set_selected.apply(this, arguments);
            this.ms_changing_selected = false;
        },
        export_as_JSON: function () {
            var json = _super_order_line.export_as_JSON.apply(this, arguments);
            json.line_qty_returned = this.line_qty_returned;
            json.original_line_id = this.original_line_id;
            json.order_uid = this.order.uid;
            json.uid = this.uid;
            json.ms_info = this.ms_info;
            return json;
        },
        // pos_multi_session | pos_multi_session_restaurant
        get_line_diff_hash: function () {
            if (this.get_note()) {
                return this.uid + '|' + this.get_note();
            } else {
                return '' + this.uid;
            }
        },
    });

    var PaymentlineSuper = models.Paymentline.prototype;

    models.Paymentline = models.Paymentline.extend({
        initialize: function (attributes, options) {
            this.pos = options.pos;
            this.order = options.order;
            this.amount = 0;
            this.selected = false;
            if (options.json) {
                this.init_from_JSON(options.json);
                return;
            }
            this.cashregister = options.cashregister;
            this.name = this.cashregister.journal_id[1];
        },
        init_from_JSON: function (json) {

            PaymentlineSuper.init_from_JSON.apply(this, arguments);
            this.payment_reference = json.payment_reference;
        },
        export_as_JSON: function () {
            return _.extend(PaymentlineSuper.export_as_JSON.apply(this, arguments), {
                payment_reference: this.payment_reference
            });
        },
        set_cashier: function () {
            PaymentlineSuper.set_cashier.apply(this, arguments);
            this.trigger('change:cashier', this);
        },
        set_payment_reference: function (reference) {
            this.payment_reference = reference;
            this.trigger('change:payment_reference', this);
        },
        get_payment_reference: function () {
            return this.payment_references
        }
    });

});
