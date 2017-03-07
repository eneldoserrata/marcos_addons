odoo.define('ncf_pos.screens', function(require) {
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var gui = require('point_of_sale.gui');

    var QWeb = core.qweb;
    var _t = core._t;

    screens.PaymentScreenWidget.include({
        validate_client: function() {
            var order = this.pos.get_order();
            var client = order.get_client();

            if (!client) {
                return "¡Debe seleccionar un cliente para validar la factura!";
            }

            if (!order.fiscal_position) {
                return "La orden no tiene tipo de comprobante asignada.";
            }

            if (order.fiscal_position.sale_fiscal_type != 'final' && !client.vat) {
                return "La posicion fiscal del cliente seleccionado requiere RNC/Cédula. Acceda al cliente y agregue esta informacion";

            } else {
            return true;
            }
        },
        validate_order: function(force_validation) {
            var self = this;
            var res = self.validate_client();

            if (res !== true) {
                self.gui.show_popup('confirm', {
                    title: _t('Por favor corrija los datos'),
                    body:  _t(res),
                    confirm: function() {
                        self.gui.close_popup();
                    }
                });
            } else {
                if (res) {
                    if (this.order_is_valid(force_validation)) {
                        this.finalize_validation();
                        }
                }
            }
        },
    });
});
