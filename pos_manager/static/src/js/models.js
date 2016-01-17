odoo.define('pos_manager.models', function (require) {

    var models = require('point_of_sale.models');

    models.load_models({
        model: 'pos.manager',
        fields: ['allow_refund', 'allow_payments', 'allow_delete_order', 'allow_discount',
            'allow_edit_price', 'allow_delete_order_line', 'allow_cancel', 'allow_cash_refund', 'users'],
        loaded: function (self, managers) {
            self.managers = managers;
        }
    });

    var PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            PosModelSuper.prototype.initialize.apply(this, arguments);
        },
        set_cashier: function (user) {
            this.cashier = user;
            this.chrome.check_allow_delete_order();
        }
    });

});
