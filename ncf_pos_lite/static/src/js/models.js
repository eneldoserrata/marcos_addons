odoo.define('ncf_pos_lite.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var Model = require('web.DataModel');
    var bus = require('bus.bus');
    var session = require('web.session');
    var Keypad = require('ncf_pos_lite.keyboard');

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
        initialize: function (session, attributes) {
            var self = this;
            this.keypad = new Keypad.Keypad({'pos': this});
            _super_posmodel.initialize.apply(this, arguments);

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
