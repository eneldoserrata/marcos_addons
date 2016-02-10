odoo.define('ipf_manager.screens', function (require) {

    var screens = require('point_of_sale.screens');
    var Model = require('web.DataModel');
    var web_data = require('web.data');


    screens.ReceiptScreenWidget.include({
        print_xml: function () {
            var self = this;
            var order = self.pos.get_order();
            var print_ready ={};

            if (self.pos.config.iface_fiscal_printer) {

                new Model('pos.order').call("get_fiscal_data", [order.name]).then(function (result) {


                    order.set_ncf(result.ncf);

                     var ipf_invoice = {
                        type: result.fiscal_type,
                        copy: self.pos.config.iface_fiscal_printer_copy,
                        cashier: self.pos.user.id,
                        subsidiary: self.pos.config.iface_fiscal_printer_subsidiary[0],
                        ncf: result.ncf || "Documento de no venta",
                        reference_ncf: order.get_credit_ncf() || "",
                        client: order.get_client().name,
                        rnc: order.get_client().vat || "",
                        items: [],
                        payments: [],
                        discount: false,
                        charges: false,
                        comments: [self.pos.config.receipt_footer || ''],
                        host: self.pos.config.iface_fiscal_printer_host,
                        invoice_id: result.id
                    };


                    order.orderlines.each(function (orderline) {
                        var line = orderline.export_as_JSON();
                        var product = self.pos.db.get_product_by_id(line.product_id);
                        var tax = orderline.get_taxes();

                        if (tax.length != 1) {
                            self.pos.gui.show_popup('error', {
                                'title': 'Error en el impuesto del producto',
                                'body': 'La impresora fiscal no admite productos con mas de un impuesto. [' +product.display_name+ ']'
                            });
                            return
                        } else if (!$.inArray(tax, [0, 5, 8, 11, 13, 18])) {
                            self.pos.gui.show_popup('error', {
                                'title': 'Error en el impuesto del producto',
                                'body': 'Tiene un porciento de ITBIS no admitido. [' +product.display_name+ ']'
                            });
                            return
                        } else {
                            var itbis = tax[0].amount
                        }


                        var ifp_line = {
                            description: product.display_name,
                            extra_description: [line.note || ""],
                            quantity: line.qty,
                            price: line.price_unit || 0,
                            itbis: itbis,
                            discount: line.discount || false,
                            charges: false
                        };
                        ipf_invoice.items.push(ifp_line)

                    });


                    order.paymentlines.each(function (paymentline) {
                        var journal_type = paymentline.ipf_payment_type || "other";
                        ipf_payment = {
                            type: journal_type,
                            amount: paymentline.amount,
                            description: false
                        };

                        ipf_invoice.payments.push(ipf_payment)
                    });

                    return ipf_invoice

                }).then(function(ipf_invoice){
                    var context = new web_data.CompoundContext({
                        active_model: "pos.order",
                        active_id: ipf_invoice.id
                    });
                    self.pos.proxy.print_receipt([ipf_invoice, context]);
                    self.pos.get_order()._printed = true;
                })

            } else {
                this._super();
            }

        }
    });

});

