odoo.define('ncf_pos_lite.chrome', function (require) {
    "use strict";

    var chrome = require('point_of_sale.chrome');


    chrome.Chrome.include({
        init: function () {
            var self = this;
            this._super.apply(this, arguments);
            this.pos.bind('change:selectedOrder', this.check_allow_delete_order, this);
            this.pos.bind('change:cashier', this.check_allow_delete_order, this);

        },
        build_chrome: function () {
            this._super();
            var self = this;
            $('.js_poll_connected').on("click", function () {
                self.sync_all_orders();
                self.chrome.gui.show_screen('kitchen_screen', {}, 'refresh');
            })

        },
        check_allow_delete_order: function () {
            var user = this.pos.cashier || this.pos.user;
            var order = this.pos.get_order();
            if (order) {
                // User option calls "Allow remove non-empty order". So we got to check if its empty we can delete it.
                if (!user.allow_delete_order && order.orderlines.length > 0) {
                    this.$('.deleteorder-button').hide();
                } else {
                    this.$('.deleteorder-button').show();
                }
            }
        },
        check_allow_add_order: function () {
            var user = this.pos.cashier || this.pos.user;
            var order = this.pos.get_order();
            if (order) {
                if (!user.allow_add_order) {
                    this.$('.neworder-button').hide();
                } else {
                    this.$('.neworder-button').show();
                }
            }
        },
        loading_hide: function () {
            this._super();
            //extra checks on init
            this.check_allow_delete_order();
            this.check_allow_add_order();
        }
    });

    chrome.OrderSelectorWidget.include({
        init: function (parent, options) {
            this._super(parent, options);
            this.pos.get('orders').bind('change:update_new_order', this.renderElement, this);
        },
        destroy: function () {
            this.pos.get('orders').unbind('change:update_new_order', this.renderElement, this);
            this._super();
        },
        renderElement: function () {
            var self = this;
            this._super();
            this.chrome.check_allow_delete_order();
            this.chrome.check_allow_add_order();

            this.$('.order-button.select-order').dblclick(function (event) {
                $(".deleteorder-button").trigger("click");
            });
        }
    });

    chrome.StatusWidget.include({
        set_poll_status: function (status) {
            var element = $('.js_poll_connected');
            if (status) {
                element.removeClass('oe_red');
                element.addClass('oe_green');
            } else {
                element.removeClass('oe_green');
                element.addClass('oe_red');
            }
        }
    });
});