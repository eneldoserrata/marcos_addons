odoo.define('ncf_pos_premium.pos_kitchen', function (require) {
    // var pos_sync_order = require('pos_sync_order');
    var session = require('web.session');
    var Backbone = window.Backbone;
    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var models = require('point_of_sale.models');
    var bus = require('bus.bus');
    var gui = require('point_of_sale.gui');
    var chrome = require('point_of_sale.chrome')
    var PosPopWidget = require('point_of_sale.popups');
    var QWeb = core.qweb;
    var _t = core._t;


    var KitchenScreenWidget = PosBaseWidget.extend({
        template: 'KitchenScreenWidget',
        init: function (parent, options) {
            this._super(parent, options);
            if (this.pos.config.pos_kitchen_view) {
                var orders = this.pos.get("orders");
                orders.bind('add remove change', this.renderElement, this);
            }
        },
        renderElement: function () {
            var self = this;
            this._super();

            this.$(".button_cooked").click(function () {
                var id = parseInt($(this).attr("data-id"));
                var order_line_id = parseInt($(this).attr("data-orderline_id"))
                kitchen_data[id].lines[order_line_id][2].order_line_status = 1;
                var data = kitchen_data[id]
                self.pos.sync_session.send({'action': 'update_order', 'order': data});
                self.pos.chrome.gui.show_screen('kitchen_screen', {}, 'refresh');
            });
            this.$(".button_delivered").click(function () {
                var id = parseInt($(this).attr("data-id"));
                var order_line_id = parseInt($(this).attr("data-orderline_id"))
                var data = kitchen_data[id]
                kitchen_data[id].lines[order_line_id][2].order_line_status = 2;
                self.pos.sync_session.send({'action': 'update_order', 'order': data});
                self.pos.chrome.gui.show_screen('kitchen_screen', {}, 'refresh');

            });
            this.$(".wv_print").click(function () {
                var id = parseInt($(this).attr("data-id"));
                var data = kitchen_data[id];
                var env = {
                    widget: self,
                    data: data,
                };
                var receipt = QWeb.render('XmlKitchenReceipt', env);
                self.pos.proxy.print_receipt(receipt);
            });

        },
        show: function () {
            var self = this;
            this._super();
        },
        close: function () {
        },
        get_product_by_id: function (id) {
            return this.pos.db.get_product_by_id(id).display_name;
        },

        get_partner_by_id: function (id) {
            return this.pos.db.get_partner_by_id(id);
        },
    });

    gui.define_screen({
        'name': 'kitchen_screen',
        'widget': KitchenScreenWidget,
    });

    chrome.Chrome.include({
        build_widgets: function () {
            var self = this;
            this._super();
            if (this.pos.config.pos_kitchen_view) {
                setTimeout(function () {
                    self.gui.show_screen('kitchen_screen');
                }, 5);
            }
        }
    });

    var PriorityPopupWidget = PosPopWidget.extend({
        template: 'PriorityPopupWidget',

        renderElement: function () {
            this._super();
            var self = this;
            $(".change_priorty").click(function () {
                var order = self.pos.get_order();
                order.order_priority = $(".priority_state").val();
                self.pos.sync_session.send({
                    'action': 'update_order',
                    'order': self.pos.get('selectedOrder').export_as_JSON()
                });
                self.click_cancel();
            });
        },
        show: function (options) {
            this.options = options || {};
            var self = this;
            this._super(options);
            this.renderElement();
        },
    });

    // gui.define_popup({
    //     'name': 'priority-popup',
    //     'widget': PriorityPopupWidget,
    // });

    var WVOrderPriorityeButton = screens.ActionButtonWidget.extend({
        template: 'WVOrderPriorityeButton',
        button_click: function () {
            var order = this.pos.get_order();
            this.gui.show_popup("selection", {
                title: "Prioridad",
                list: [
                    {label: 'Normal', item: 0},
                    {label: 'Media', item: 1},
                    {label: 'Alta', item: 2}
                ],
                confirm: function (item) {
                    order.order_priority = item;

                }
            });

            // if (order) {
            //     this.gui.show_popup('priority-popup', {'order_priority': order.order_priority});
            // }
        }
    });

    screens.define_action_button({
        'name': 'order_priority',
        'widget': WVOrderPriorityeButton,
        'condition': function () {
            return true;//this.pos.config.wv_allow_order_priority;
        }
    });
});
