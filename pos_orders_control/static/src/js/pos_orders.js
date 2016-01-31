odoo.define('pos_orders.pos_orders', function (require) {
    "use strict";
    var Model = require('web.DataModel');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var utils = require('web.utils');
    var core = require('web.core');
    var QWeb = core.qweb;


    var OrdersScreenWidget = screens.ScreenWidget.extend({
        template: 'OrdersScreenWidget',

        init: function (parent, options) {
            this._super(parent, options);
        },
        render_list: function (intput_txt) {
            var self = this;
            self.wk_orders = [];
            var posOrderModel = new Model('pos.order');


            posOrderModel.call('wk_order_list', [intput_txt])
                .then(function (order_data) {
                    if (order_data.length > 0) {
                        self.wk_orders = order_data;
                    }
                })
                .then(function () {
                    var contents = self.$el[0].querySelector('.wk-order-list-contents');
                    var cashier = self.pos.get_cashier();
                    contents.innerHTML = "";

                    if (self.wk_orders.length > 0) {
                        _.each(self.wk_orders, function (order) {

                            var orderline_html = QWeb.render('WkOrderLine', {widget: this, order: order});
                            var orderline = document.createElement('tbody');
                            orderline.innerHTML = orderline_html;
                            orderline = orderline.childNodes[1];

                            $(orderline).find(".wk_reorder_content").click(function () {
                                self.reorder(this)
                            });

                            $(orderline).find(".wk_reprint_content").click(function () {
                                self.reprint(this)
                            });

                            if (!cashier.allow_refund) {
                                $(orderline).find(".wk_refund_content").css('visibility', 'hidden');
                            } else {
                                $(orderline).find(".wk_refund_content").css('visibility', 'visible');
                                $(orderline).find(".wk_refund_content").click(function () {
                                    self.refund(this)
                                });
                            }

                            contents.appendChild(orderline);

                        });
                    }

                });

        },
        show: function () {
            var self = this;
            this._super();

            this.$('.order_search').keyup(function () {
                if ($(this).val()) {
                    self.render_list(this.value);
                }

            }).focus();

            this.$('.back').click(function () {
                self.gui.show_screen('products');
            });

        },
        close: function () {
            this._super();
            this.$('.wk-order-list-contents').undelegate();
            this.$('.order_search').val("");
            this.$('.wk-order-list-contents').empty()

        },
        get_wk_order: function (button, type) {
            var self = this;
            var wk_order = [];
            var wk_lines = [];
            _.each(self.wk_orders, function (rec) {
                if (rec.id == button.id) {
                    wk_order = rec;
                }
            });

            _.each(wk_order.lines, function (line) {
                wk_lines.push([false, false, {
                    product_id: line.product_id,
                    price_unit: line.price_unit,
                    discount: line.discount,
                    qty: line.qty,
                    id: line.id
                }])

            });

            var order = new models.Order({}, {
                pos: self.pos,
                json: {
                    sequence_number: 0,
                    session_id: wk_order.session_id,
                    uid: wk_order.uid,
                    partner_id: wk_order.partner_id,
                    lines: wk_lines,
                    statement_ids: []
                }
            });

            order.uid = order.generate_unique_id()

            return order

        },
        reorder: function (button) {
            var self = this;
            var wk_order = [];
            _.each(self.wk_orders, function (rec) {
                if (rec.id == button.id) {
                    wk_order = rec;
                }
            });

            var order = self.pos.get_order();

            _.each(wk_order.lines, function (line) {
                var product = self.pos.db.get_product_by_id(line.product_id);
                order.add_product(product, {quantity: line.qty});
            });

            self.gui.show_screen('products');

        },
        reprint: function (button) {
            var self = this;
            var order = self.get_wk_order(button, "reprint");
            self.gui.back();
            self.pos.set('selectedOrder', order);
            self.gui.show_screen('receipt');
        },
        refund: function (button) {
            var self = this;
            var wk_order = [];
            _.each(self.wk_orders, function (rec) {
                if (rec.id == button.id) {
                    wk_order = rec;
                }
            });
            self.gui.show_screen('products');

            var products = [];
            _.each(wk_order.lines, function (line) {
                if (line.qty_allow_refund > 0) {
                    var product = self.pos.db.get_product_by_id(line.product_id);
                    product.qty_allow_refund = line.qty_allow_refund;
                    product.refund_price = line.price_unit;
                    product.refund_discount = line.discount;
                    product.refund_note = line.note;
                    product.refund_line_ref = line.id;
                    products.push(product);
                }
            });

            self.pos.add_new_order();
            var order = self.pos.get_order();
            var partner = self.pos.db.get_partner_by_id(wk_order.partner_id[0].id);
            order.set_order_type("refund");
            order.set_origin(button.id);
            order.set_client(partner);
            order.set_origin_ncf(wk_order.origin_ncf);
            self.pos.set_order(order);
            self.pos.gui.screen_instances.products.product_list_widget.set_product_list(products);
            order.save_to_db();

        }
    });

    gui.define_screen({name: 'wk_orders', widget: OrdersScreenWidget});

    var OrdersButtonWidget = screens.ActionButtonWidget.extend({
        template: 'OrdersButtonWidget',
        button_click: function () {
            var self = this;
            self.gui.show_screen('wk_orders');

        }
    });

    screens.define_action_button({
        'name': 'All Orders',
        'widget': OrdersButtonWidget,
        'condition': function () {
            return true;
        }
    });

    return OrdersScreenWidget;
});


