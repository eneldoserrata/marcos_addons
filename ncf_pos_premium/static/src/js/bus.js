odoo.define('ncf_pos_premium.pos_longpolling', function (require) {

    var exports = {};

    var Backbone = window.Backbone;
    var core = require('web.core');
    var bus = require('bus.bus');
    var _t = core._t;

    // prevent bus to be started by chat_manager.js
    bus.bus.activated = true; // fake value to ignore start_polling call

    exports.LongpollingConnection = Backbone.Model.extend({
        initialize: function (pos) {
            this.pos = pos;
            this.timer = false;
            this.status = false;
            this.response_status = false; // Is the message "PONG" received from the server
        },
        network_is_on: function (message) {
            if (message) {
                this.response_status = true;
            }
            this.update_timer();
            this.set_status(true);
        },
        network_is_off: function () {
            this.update_timer();
            this.set_status(false);
        },
        set_status: function (status) {
            if (this.status == status) {
                return;
            }
            this.status = status;
            this.trigger("change:poll_connection", status);
        },
        update_timer: function () {
            this.stop_timer();
            this.start_timer(this.pos.config.query_timeout, 'query');
        },
        stop_timer: function () {
            var self = this;
            if (this.timer) {
                clearTimeout(this.timer);
                this.timer = false;
            }
        },
        start_timer: function (time, type) {
            var time = Math.round(time * 3600.0);
            var self = this;
            this.timer = setTimeout(function () {
                if (type == "query") {
                    self.send();
                } else if (type == "response") {
                    // if (self.pos.debug) {
                    //     console.log('POS LONGPOLLING start_timer error', self.pos.config.name);
                    // }
                    self.network_is_off();
                }
            }, time * 1000);
        },
        response_timer: function () {
            this.stop_timer();
            this.start_timer(this.pos.config.response_timeout, "response");
        },
        send: function () {

            var self = this;
            this.response_status = false;
            openerp.session.rpc("/pos_longpolling/update", {
                message: "PING",
                pos_id: self.pos.config.id
            }).then(function () {
                /* If the value "response_status" is true, then the poll message came earlier
                if the value is false you need to start the response timer*/
                if (!self.response_status) {
                    self.response_timer();
                }
            }, function (error, e) {
                e.preventDefault();
                // if (self.pos.debug) {
                //     console.log('POS LONGPOLLING send error', self.pos.config.name);
                // }
                self.network_is_off();
            });

        }
    });

    exports.MultiSession = Backbone.Model.extend({
        initialize: function (pos) {
            var self = this;
            this.pos = pos;
            this.client_online = true;
            this.order_ID = null;
            this.update_queue = $.when();
            this.func_queue = [];
            this.pos.longpolling_connection.on("change:poll_connection", function (status) {
                if (status) {
                    if (self.offline_sync_all_timer) {
                        clearInterval(self.offline_sync_all_timer);
                        self.offline_sync_all_timer = false;
                    }
                    self.request_sync_all();
                } else {
                    if (!self.offline_sync_all_timer) {
                        self.no_connection_warning();
                        self.start_offline_sync_timer();
                        // if (self.pos.debug) {
                        //     console.log('MultiSession initialize error');
                        // }
                    }
                }
            });
        },
        request_sync_all: function () {
            var data = {};
            return this.send({'action': 'sync_all', data: data});
        },
        remove_order: function (data) {
            this.send({action: 'remove_order', data: data});
        },
        update: function (data) {
            return this.send({action: 'update_order', data: data});
        },
        enque: function (func) {
            var self = this;
            this.func_queue.push(func);
            this.update_queue = this.update_queue.then(function () {
                if (self.func_queue[0]) {
                    var next = $.Deferred();
                    var func1 = self.func_queue.shift();
                    func1().always(function () {
                        next.resolve()
                    });
                    return next;
                }
            })
        },
        _debug_send_number: 0,
        send: function (message) {
            var current_send_number = 0;
            // if (this.pos.debug) {
            //     current_send_number = this._debug_send_number++;
            //     console.log('MS', this.pos.config.name, 'send #' + current_send_number + ' :', JSON.stringify(message));
            // }
            var self = this;
            message.data.pos_id = this.pos.config.id;
            var send_it = function () {
                return openerp.session.rpc("/pos_multi_session/update", {
                    multi_session_id: self.pos.config.multi_session_id[0],
                    message: message
                });
            };
            return send_it().fail(function (error, e) {
                // if (self.pos.debug) {
                //     console.log('MS', self.pos.config.name, 'failed request #' + current_send_number + ':', error.message);
                // }
                if (error.message === 'XmlHttpRequestError ') {
                    self.client_online = false;
                    e.preventDefault();
                    self.pos.longpolling_connection.network_is_off();
                    if (!self.offline_sync_all_timer) {
                        // if (self.pos.debug) {
                        //     console.log('send, return send_it error');
                        // }
                        self.no_connection_warning();
                        self.start_offline_sync_timer();
                    }
                } else {
                    self.request_sync_all();
                }
            }).done(function (res) {
                // if (self.pos.debug) {
                //     console.log('MS', self.pos.config.name, 'response #' + current_send_number + ':', JSON.stringify(res));
                // }
                var server_orders_uid = [];
                self.client_online = true;

                if (res.action == "revision_error") {
                    var warning_message = _t('There is a conflict during synchronization, try your action again');
                    self.warning(warning_message);
                    self.request_sync_all();
                }
                if (res.action == 'sync_all') {
                    res.orders.forEach(function (item) {
                        self.pos.ms_on_update(item, true);
                        server_orders_uid.push(item.data.uid);
                    });
                    self.pos.pos_session.order_ID = res.order_ID;

                    if (res.order_ID != 0) {
                        self.pos.pos_session.sequence_number = res.order_ID;
                    }
                    self.destroy_removed_orders(server_orders_uid);
                }
                if (self.offline_sync_all_timer) {
                    clearInterval(self.offline_sync_all_timer);
                    self.offline_sync_all_timer = false;
                }
            });
        },
        destroy_removed_orders: function (server_orders_uid) {
            var self = this;
            // find all client orders whose order_on_server is True
            var orders = self.pos.get('orders').filter(
                function (r) {
                    return (r.order_on_server === true);
                }
            );
            /* if found by the order from the client is not on the
            list server orders then is means the order was deleted */
            orders.forEach(function (item) {
                var remove_order = server_orders_uid.indexOf(item.uid);
                if (remove_order === -1) {
                    var order = self.pos.get('orders').find(function (order) {
                        return order.uid == item.uid;
                    });
                    order.destroy({'reason': 'abandon'});
                }
            });
            self.send_offline_orders();
        },
        warning: function (warning_message) {
            this.pos.chrome.gui.show_popup('error', {
                'title': _t('Warning'),
                'body': warning_message,
            });
        },
        send_offline_orders: function () {
            var self = this;
            var orders = this.pos.get("orders");
            orders.each(function (item) {
                if (!item.order_on_server && item.get_orderlines().length > 0) {
                    item.ms_update();
                }
            });
        },
        start_offline_sync_timer: function () {
            var self = this;
            self.offline_sync_all_timer = setInterval(function () {
                self.request_sync_all();
            }, 5000);
        },
        no_connection_warning: function () {
            var warning_message = _t("No connection to the server. You can create new orders only. It is forbidden to modify existing orders.");
            this.warning(warning_message);
        }
    });

    return exports;
});
