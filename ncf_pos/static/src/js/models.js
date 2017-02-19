odoo.define('ncf_pos.models', function(require) {
    'use strict';

    var models = require('point_of_sale.models');
    var session = require('web.session');
    var Model = require('web.DataModel');

    models.load_fields("product.product", ["tracking"]);
    models.load_fields("res.company", ['street', 'street2', "city", 'state_id', 'zip', 'country_id']);
    models.load_fields("res.partner", ['property_account_position_id']);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments);
            var self = this;
            this.to_invoice = false;
            this.order_type = this.order_type || "order";
            this.origin = this.origin || false;
            this.origin_ncf = this.origin_ncf || false;
            this.ncf = this.ncf || "";
            this.invoice_type = this.invoice_type || "";
            this.fiscal_type = this.fiscal_type || "";

            if (!self.get_client()) {
                var default_partner_id = self.pos.db.get_partner_by_id(self.pos.config.default_partner_id[0]);
                self.set_client(default_partner_id);
            }
        },
        set_client: function(client) {
            var self = this;

            if (client) {
                _.each(self.pos.fiscal_positions, function(fiscal_position) {
                    if (client.property_account_position_id) {
                        if (fiscal_position.id === client.property_account_position_id[0]) {
                            self.fiscal_position = fiscal_position;
                        }
                    } else if (fiscal_position.client_fiscal_type === "final") {
                        self.fiscal_position = fiscal_position;
                    }
                });
            }
            this.assert_editable();
            this.set('client', client);
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments);
            this.to_invoice = json.to_invoice;
            this.order_type = json.order_type;
            this.origin = json.origin;
            this.origin_ncf = json.origin_ncf;
            return this;
        },
        set_to_invoice: function(to_invoice) {
            this.assert_editable();
            this.to_invoice = false;
            this.trigger('change', this);
        },
        get_to_invoice: function(){
            return this.to_invoice || true;
        },
        set_order_type: function(order_type) {
            this.order_type = order_type;
            this.trigger('change', this);
        },
        get_order_type: function() {
            return this.order_type || "order";
        },
        set_origin: function(origin) {
            this.origin = origin;
            this.trigger('change', this);
        },
        get_origin: function() {
            return this.origin || false;
        },
        set_ncf: function(ncf) {
            this.ncf = ncf;
            this.trigger('change', this);
        },
        get_ncf: function() {
            return this.ncf || false;
        },
        set_fiscal_type_name: function(fiscal_type_name) {
            this.fiscal_type_name = fiscal_type_name;
            this.trigger('change', this);
        },
        get_fiscal_type_name: function() {
            return this.fiscal_type_name || false;
        },
        set_origin_ncf: function(origin_ncf) {
            this.origin_ncf = origin_ncf;
            this.trigger('change', this);
        },
        get_origin_ncf: function() {
            return this.origin_ncf || false;
        },
        set_fiscal_type: function(credit) {
            this.fiscal_type = credit;
            this.trigger('change', this);
        },
        get_fiscal_type: function() {
            return this.fiscal_type || 0;
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.to_invoice = this.get_to_invoice();
            json.order_type = this.get_order_type();
            json.origin = this.get_origin();
            json.origin_ncf = this.get_origin_ncf();
            json.ncf = this.get_ncf();
            json.fiscal_type_name = this.get_fiscal_type_name();
            json.fiscal_type = this.get_fiscal_type();
            return json;
        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments);
            json.to_invoice = this.get_to_invoice();
            json.order_type = this.get_order_type();
            json.origin = this.get_origin();
            json.origin_ncf = this.get_origin_ncf();
            json.ncf = this.get_ncf();
            json.fiscal_type_name = this.get_fiscal_type_name();
            json.fiscal_type = this.get_fiscal_type();
            return json;
        }
    });
});
