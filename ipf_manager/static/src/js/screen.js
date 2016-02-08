odoo.define('ipf_manager.screens', function (require) {

    var screens = require('point_of_sale.screens');
    var Model = require('web.DataModel');


    screens.ReceiptScreenWidget.include({
        print_xml: function () {
            var self = this;
            var order = this.pos.get_order();

            if (this.pos.config.iface_fiscal_printer) {

                //var env = {
                //    widget: this,
                //    pos: this.pos,
                //    order: this.pos.get_order(),
                //    receipt: this.pos.get_order().export_for_printing(),
                //    paymentlines: this.pos.get_order().get_paymentlines()
                //};


                ipf_invoice = {
                    type: order.get_fiscal_type(),
                    copy: self.pos.config.iface_fiscal_printer_copy,
                    cashier: self.pos.user.id,
                    subsidiary: self.pos.config.iface_fiscal_printer_subsidiary[0],
                    ncf: order.get_ncf(),
                    reference_ncf: order.get_credit_ncf(),
                    client: order.get_client().name,
                    rnc: false,
                    items: [],
                    payments: [],
                    discount: false,
                    charges: false,
                    comments: false
                };

                ifp_line = {
                    description: false,
                    extra_description: false,
                    quantity: false,
                    price: false,
                    itbis: false,
                    discount: false,
                    charges: false
                };

                ipf_payment = {
                    type: false,
                    amount: false,
                    description: false
                };

                console.log("================")
                console.log(ipf_invoice);
                console.log("================")


            } else {
                this._super();
            }
            ;
        }
    });

})

