odoo.define('ipf_manager.models', function (require) {
    'use strict';
    var models = require('point_of_sale.models');
    models.load_fields('account.journal', 'ipf_payment_type');


    models.load_models({
        model: 'ipf.printer.config',
        fields: ["host", 'print_source', 'print_copy', 'subsidiary'],
        domain: function (self) {
            return [['id', '=', self.config.iface_fiscal_printer[0]]];
        },
        loaded: function (self, configs) {
            if (configs.length > 0) {
                self.config.iface_fiscal_printer_host = configs[0].host || false;
                self.config.iface_fiscal_printer_source = configs[0].print_source || false;
                self.config.iface_fiscal_printer_copy = configs[0].print_copy || false;
                self.config.iface_fiscal_printer_subsidiary = configs[0].subsidiary || false;
            }
        },


    });
});



