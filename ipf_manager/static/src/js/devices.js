odoo.define('ipf_manager.devices', function (require) {

    var devices = require('point_of_sale.devices');

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
        //print_receipt: function (receipt) {
        //    var self = this;
        //    if (this.pos.config.iface_fiscal_printer) {
        //        console.log("=======iface_fiscal_printer=========")
        //        console.log(receipt)
        //        console.log("================")
        //    } else {
        //        return this._super(receipt);
        //    }

        //    function send_printing_job() {
        //        if (self.receipt_queue.length > 0) {
        //            var r = self.receipt_queue.shift();
        //            self.message('print_xml_receipt', {receipt: r}, {timeout: 5000})
        //                .then(function () {
        //                    send_printing_job();
        //                }, function (error) {
        //                    if (error) {
        //                        self.pos.chrome.screen_selector.show_popup('error-traceback', {
        //                            'title': _t('Printing Error: ') + error.data.message,
        //                            'body': error.data.debug,
        //                        });
        //                        return;
        //                    }
        //                    self.receipt_queue.unshift(r);
        //                });
        //        }
        //    }
        //
        //    send_printing_job();
        //}
    });

});