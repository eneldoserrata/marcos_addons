odoo.define('ipf_manager.devices', function (require) {


    var devices = require('point_of_sale.devices');
    var IpfApi = require('ipf_manager.service');
    var web_data = require('web.data');
    var Model = require('web.DataModel');
    var gui = require('point_of_sale.gui');
    var PopupWidget = require("point_of_sale.popups");
    var screens = require('point_of_sale.screens');

    devices.ProxyDevice.include({
        try_hard_to_connect: function (url, options) {
            var self = this;

            if (this.pos.config.iface_fiscal_printer) {
                options = options || {};

                self.set_connection_status('connecting');

                var url = self.pos.config.iface_fiscal_printer_host;

                function try_real_hard_to_connect(url, retries, done) {

                    done = done || new $.Deferred();

                    $.ajax({
                        url: url + "/state",
                        method: 'GET',
                        timeout: 1000
                    })
                        .done(function () {
                            done.resolve(url);
                        })
                        .fail(function () {
                            if (retries > 0) {
                                try_real_hard_to_connect(url, retries - 1, done);
                            } else {
                                done.reject();
                            }
                        });
                    return done;
                }

                return try_real_hard_to_connect(url, 3);


            } else {
                return this._super(url, options)
            }

        },
        connect: function (url) {
            var self = this;

            if (this.pos.config.iface_fiscal_printer) {
                var url = self.pos.config.iface_fiscal_printer_host;
                return $.ajax({type: "GET", url: url + "/software_version"})
                    .done(function (response) {
                        self.set_connection_status('connected');
                        localStorage.hw_proxy_url = url;
                        self.keepalive();
                    })
                    .fail(function (response) {
                        self.set_connection_status('disconnected');
                        console.error('Connection refused by the Proxy');
                    });

            } else {
                return this._super(url);
            }
        },
        keepalive: function () {
            var self = this;
            if (this.pos.config.iface_fiscal_printer) {
                function status() {
                    var url = self.pos.config.iface_fiscal_printer_host;
                    return $.ajax({type: "GET", url: url + "/state", timeout: 2500})
                        .done(function () {
                            var driver_status = {escpos: {status: "connected"}};
                            self.set_connection_status('connected', driver_status);
                        })
                        .fail(function () {
                            if (self.get('status').status !== 'connecting') {
                                self.set_connection_status('disconnected');
                            }
                        })
                        .always(function () {
                            setTimeout(status, 5000);
                        });
                }

                if (!this.keptalive) {
                    this.keptalive = true;
                    status();
                }

            } else {
                this._super();
            }

        },
        ipf_get_pos_data: function () {
            var self = this;
            var order = self.pos.get_order();
            var partner = order.get_client();

            var comments = $.trim("==================NOTA==================" + order.name || "" + order.get_order_note() || "" + self.pos.config.receipt_footer || '' + "========================================");
            var comments_list = comments.match(/.{1,40}/g);

            var ipf_invoice = {
                type: "nofiscal",
                copy: self.pos.config.iface_fiscal_printer_copy,
                cashier: self.pos.user.id,
                subsidiary: self.pos.config.iface_fiscal_printer_subsidiary[0],
                ncf: "Documento de no venta",
                reference_ncf: "",
                client: partner.name,
                rnc: partner.vat,
                items: [],
                payments: [],
                discount: false,
                charges: false,
                comments: comments_list,
                host: self.pos.config.iface_fiscal_printer_host,
                invoice_id: false,
                total_invoice: 0,
            };

            var fractions = self.pos.get("fractions");

            order.orderlines.each(function (orderline) {
                var line = orderline.export_as_JSON();
                var product = self.pos.db.get_product_by_id(line.product_id);
                var tax = orderline.get_taxes();

                if (tax.length != 1) {
                    self.pos.gui.show_popup('error', {
                        'title': 'Error en el impuesto del producto',
                        'body': 'La impresora fiscal no admite productos con mas de un impuesto. [' + product.display_name + ']'
                    });
                    return
                } else if (!$.inArray(tax, [0, 5, 8, 11, 13, 18])) {
                    self.pos.gui.show_popup('error', {
                        'title': 'Error en el impuesto del producto',
                        'body': 'Tiene un porciento de ITBIS no admitido. [' + product.display_name + ']'
                    });
                    return
                } else {
                    var itbis = tax[0].amount
                }

                var nota = (typeof line.note === "undefined" ? "" : " " + line.note);

                var quantity = line.qty;
                var price = line.price_unit || 0;
                var fraction_name = "";

                if (quantity < 1 && fractions != undefined) {
                    _.each(fractions, function (fraction) {
                        if (fraction.qty == quantity) {
                            fraction_name = fraction.name + " ";
                        } else {
                            fraction_name = quantity + " ";
                        }
                    });
                    price = quantity * price;
                    quantity = 1;
                }
                var description = $.trim(fraction_name + product.display_name + nota);

                var description_list = description.match(/.{1,21}/g);

                var ifp_line = {
                    description: description_list.pop(),
                    extra_descriptions: description_list,
                    quantity: quantity,
                    price: price,
                    itbis: itbis,
                    discount: line.discount || false,
                    charges: false
                };
                ipf_invoice.total_invoice += (line.price_unit * line.qty)
                ipf_invoice.items.push(ifp_line)

            });


            order.paymentlines.each(function (paymentline) {
                var journal_type = paymentline.cashregister.journal.ipf_payment_type || "other";
                var ipf_payment = {
                    type: journal_type,
                    amount: paymentline.amount,
                    description: paymentline.name
                };

                ipf_invoice.payments.push(ipf_payment)
            });


            return ipf_invoice;


        },
        ipf_nofiscal_print: function () {
            var self = this;
            var context = new web_data.CompoundContext({
                active_model: false,
                active_id: false
            });
            var ipfProxy = new IpfApi();
            var ipf_invoice = self.ipf_get_pos_data();

            ipf_invoice.payments = null
            ipf_invoice.type = "quotation"
            ipfProxy.print_receipt(ipf_invoice, context);
        },
        ipf_fiscal_print: function (order_name, fiscal_type) {
            var self = this;
            var order = self.pos.get_order();
            var ipf_invoice = self.ipf_get_pos_data();


            var ipfProxy = new IpfApi();

            return new Model('pos.order').call("get_fiscal_data", [order.name]).then(function (result) {

                ipf_invoice.type = result.fiscal_type;
                ipf_invoice.ncf = result.ncf || "Documento de no venta";
                ipf_invoice.reference_ncf = result.origin || "";
                ipf_invoice.invoice_id = result.id;
                return ipf_invoice

            }).done(function (ipf_invoice) {
                var context = new web_data.CompoundContext({
                    active_model: "pos.order",
                    active_id: ipf_invoice.id
                });

                order.destroy();
                return ipfProxy.print_receipt(ipf_invoice, context);
            })

        },
        message: function (name, params) {
            var self = this;
            var order = self.pos.get_order();

            if (self.pos.config.iface_fiscal_printer) {
                var r = params.receipt;
            } else {
                var callbacks = this.notifications[name] || [];
                for (var i = 0; i < callbacks.length; i++) {
                    callbacks[i](params);
                }
            }

            if (this.get('status').status !== 'disconnected') {
                if (self.pos.config.iface_fiscal_printer) {
                    var parse_xml_params = $.parseXML(params.receipt);
                    var order_name = $(parse_xml_params).find("ipfordername").text();
                    return self.ipf_fiscal_print(order_name, "fiscal");
                } else {
                    return this.connection.rpc('/hw_proxy/' + name, params || {});
                }
            } else {
                new Model('pos.order').call("get_fiscal_data", [order.name]);
                return (new $.Deferred()).reject();
            }
        },
        print_sale_details: function () {
            this.pos.gui.show_popup('ipfPrintReport');
        }
    });


    var IPFPrintReport = PopupWidget.extend({
        template: 'IPFPrintReport',

        events: _.extend({}, PopupWidget.prototype.events, {
            'click .ipf-cierre-z': 'ipf_cierre_z',
            'click .ipf-shift-change': 'ipf_shift_change',
            'click .ipf-report-x': 'ipf_report_x',
            'click .ipf-today-report': 'ipf_today_report',
            'click .ipf-shift-report': 'ipf_shift_report'
        }),
        ipf_cierre_z: function () {
            var self = this;
            var ipfProxy = new IpfApi();
            var context = new web_data.CompoundContext({
                active_model: "ipf.printer.config",
                active_id: self.pos.config.iface_fiscal_printer[0]
            });
            ipfProxy.get_z_close_print(context);
            this.pos.gui.close_popup();
        },
        ipf_shift_change: function () {
            var self = this;
            var ipfProxy = new IpfApi();
            var context = new web_data.CompoundContext({
                active_model: "ipf.printer.config",
                active_id: self.pos.config.iface_fiscal_printer[0]
            });
            ipfProxy.get_new_shift_print(context);
            this.pos.gui.close_popup();

        },
        ipf_report_x: function () {
            var self = this;
            var ipfProxy = new IpfApi();
            var context = new web_data.CompoundContext({
                active_model: "ipf.printer.config",
                active_id: self.pos.config.iface_fiscal_printer[0]
            });
            ipfProxy.get_x(context);
            this.pos.gui.close_popup();

        },
        ipf_today_report: function () {
            var self = this;
            var ipfProxy = new IpfApi();
            var context = new web_data.CompoundContext({
                active_model: "ipf.printer.config",
                active_id: self.pos.config.iface_fiscal_printer[0]
            });
            ipfProxy.get_information_day(context);
            this.pos.gui.close_popup();

        },
        ipf_shift_report: function () {
            var self = this;
            var ipfProxy = new IpfApi();
            var context = new web_data.CompoundContext({
                active_model: "ipf.printer.config",
                active_id: self.pos.config.iface_fiscal_printer[0]
            });
            ipfProxy.get_information_shift(context);
            this.pos.gui.close_popup();
        }
    });

    gui.define_popup({name: 'ipfPrintReport', widget: IPFPrintReport});


    var IpfPrintBillButton = screens.ActionButtonWidget.extend({
        template: 'IpfPrintBillButton',
        button_click: function () {

            this.pos.proxy.ipf_nofiscal_print()
        }
    });

    screens.define_action_button({
        'name': 'ipf_print_bill',
        'widget': IpfPrintBillButton,
        'condition': function () {
            return this.pos.config.iface_fiscal_printer;
        },
    });

});
