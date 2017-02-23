odoo.define('ncf_pos.models', function (require) {
    "use strict";

    var core = require('web.core');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var Model = require('web.DataModel');

    var QWeb = core.qweb;

    models.load_fields("res.company", ['street', 'street2', "city", 'state_id', 'zip', 'country_id']);
    models.load_fields("res.partner", ['property_account_position_id']);

    var _super_order = models.Order.prototype;

    models.Order = models.Order.extend({

        set_client: function(client) {
            var self = this;
            if (client) {
                _.each(self.pos.fiscal_positions, function(fiscal_position) {
                    if (client.property_account_position_id) {
                        if (fiscal_position.id === client.property_account_position_id[0]) {
                            self.fiscal_position = fiscal_position;
                        }
                    } else if (fiscal_position.sale_fiscal_type === "final") {
                        self.fiscal_position = fiscal_position;
                    }
                });
            }
            this.assert_editable();
            this.set('client', client);
        },
    });

    screens.ReceiptScreenWidget.include({

        ncf_render_receipt: function (fiscal_data) {
            var order = this.pos.get_order();
            order.fiscal_type_name = fiscal_data.fiscal_type_name;
            order.ncf = fiscal_data.ncf;
            this.$('.pos-receipt-container').html(QWeb.render('PosTicket', {
                widget: this,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
            }));
        },
        render_receipt: function () {
            var self = this;
            var order = this.pos.get_order();

            new Model('pos.order').call("get_fiscal_data", [order.name]).then(function (fiscal_data) {
                self.ncf_render_receipt(fiscal_data);
            });
        }
    });
});
