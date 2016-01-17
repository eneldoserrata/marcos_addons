odoo.define('pos_disable_payment', function (require) {
    "use strict";

    var chrome = require('point_of_sale.chrome');
    var screens = require('point_of_sale.screens');

    chrome.Chrome.include({
        init: function () {
            this._super.apply(this, arguments);
            this.pos.bind('change:selectedOrder', this.check_allow_delete_order, this)
        },
        check_allow_delete_order: function () {
            var self = this;
            var cashier = self.pos.get_cashier();
            var order = this.pos.get_order();
            _.each(self.pos.managers, function (manager) {
                _.each(manager.users, function (user) {
                    if (user === cashier.id) {

                        //allow_delete_order
                        if (!manager.allow_delete_order) {
                            self.$('.deleteorder-button').toggle(order.is_empty());
                        } else if (manager.allow_delete_order) {
                            self.$('.deleteorder-button').show()
                        }

                        //allow_payments
                        self.$(".button.pay").toggle(manager.allow_payments);

                        //allow_discount
                        self.$el.find("[data-mode='discount']").css('visibility', 'visible');
                        if (manager.allow_discount === 0) {
                            self.$el.find("[data-mode='discount']").css('visibility', 'hidden')
                        }

                        //allow_edit_price
                        self.$el.find("[data-mode='price']").css('visibility', 'visible');
                        if (!manager.allow_edit_price) {
                            self.$el.find("[data-mode='price']").css('visibility', 'hidden')
                        }

                        self.$el.find("[data-mode='price']").css('visibility', 'visible');
                        if (!manager.allow_refund) {
                            self.$el.find(".numpad-minus").css('visibility', 'hidden')
                        }

                    }
                })
            });
        },

        loading_hide: function () {
            this._super();
            //extra checks on init
            this.check_allow_delete_order();
        }
    });

    chrome.OrderSelectorWidget.include({
        renderElement: function () {
            this._super();
            this.chrome.check_allow_delete_order();
        }
    });

    screens.OrderWidget.include({
        bind_order_events: function () {
            this._super();
            var order = this.pos.get('selectedOrder');
            order.orderlines.bind('add remove', this.chrome.check_allow_delete_order, this.chrome)
        }
    });

    screens.NumpadWidget.include({
        clickDeleteLastChar: function () {
            var self = this;
            var cashier = self.pos.get_cashier();

            var allow_delete_order_line = true;
            _.each(self.pos.managers, function (manager) {
                _.each(manager.users, function (user) {
                    if (user === cashier.id) {
                        if (!manager.allow_delete_order_line) {
                            allow_delete_order_line = false
                        }
                    }
                })
            });

            if (this.state.get('buffer') === "" && this.state.get('mode') === 'quantity' && !allow_delete_order_line) {
                return;
            }
            return this._super();
        }
    });


});
