odoo.define('ncf_pos.screens', function(require) {
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var gui = require('point_of_sale.gui');
    var form_common = require('web.form_common');

    var QWeb = core.qweb;
    var _t = core._t;

    screens.ProductScreenWidget.include({
        start: function() {
            this._super();
            var self = this;
            var fiscal_position = self.action_buttons.set_fiscal_position;

            if (fiscal_position === undefined) {
                window.location.replace("/web");
                alert("Debe asignar posiciones fiscales a esta terminal.");
            } else {
                $(self.action_buttons.set_fiscal_position.$el).remove();
            }
        },
    });

    screens.PaymentScreenWidget.include({
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            this.keyboard_keydown_handler = function(event) {
                if (event.keyCode === 8 || event.keyCode === 46) {
                    self.keyboard_handler(event);
                }
            };
            this.keyboard_handler = function(event) {
                var key = '';
                if (event.type === "keypress") {
                    if (event.keyCode === 13) { // Enter
                        self.validate_order();
                    } else if (event.keyCode === 190 || // Dot
                        event.keyCode === 110 || // Decimal point (numpad)
                        event.keyCode === 188) { // Comma
                        key = '.';
                    } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
                        key = '' + (event.keyCode - 48);
                    } else if (event.keyCode === 45) { // Minus
                        key = '-';
                    } else if (event.keyCode === 43) { // Plus
                        key = '+';
                    }
                } else { // keyup/keydown
                    if (event.keyCode === 46) { // Delete
                        key = 'CLEAR';
                    } else if (event.keyCode === 8) { // Backspace
                        key = 'BACKSPACE';
                    }
                }
                self.payment_input(key);
            };
        },
        validate_client: function() {
            var order = this.pos.get_order();
            var client = order.get_client();

            if (order.fiscal_position === undefined) {
                return alert("El cliente no tiene posicion fiscal asignada.");
            }

            if (client === undefined) {
                return "Debe de seleccionar cliente para validar la factura!";
            } else if (order.fiscal_position.client_fiscal_type != 'final' && client.vat === false) {
                return "La posicion fiscal del cliente seleccionado requiere RNC/Cédula.";
            }
            return true;
        },
        validate_order: function(force_validation) {
            var self = this;
            var res = self.validate_client();

            if (res !== true) {
                self.gui.show_popup('confirm', {
                    title: _t('Cliente no seleccionado!'),
                    body: res,
                    confirm: function() {
                        self.gui.close_popup();
                    }
                });
            } else {
                this.order_is_valid(force_validation).then(function (res) {
                    if (res) {
                        this.finalize_validation();
                        }
                });
            }
        },
    });
});
