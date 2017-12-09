odoo.define('ncf_pos_lite.sale_order', function (require) {
    "use strict";

    var Model = require('web.DataModel');
    var screens = require('point_of_sale.screens');
    var ActionManager = require('web.ActionManager');
    var utils = require('web.utils');
    var Mutex = utils.Mutex;

    var CreateSalesOrderWidget = screens.ActionButtonWidget.extend({
        template: 'CreateSalesOrderWidget',

        button_click: function () {
            var self = this;
            var order = self.pos.get('selectedOrder');
            var client = order.get_client();
            var orderLine = order.orderlines;
            if (orderLine.length == 0) {
                self.gui.show_popup('alert', {
                    title: "LÍNEA DE PEDIDO VACÍA",
                    body: "NO HAY PRODUCTO EN LA ORDEN SELECCIONADA."
                });

            } else if (client == null) {

                self.gui.show_popup('alert', {
                    title: "Seleccione el cliente",
                    body: "Primero debe seleccionar al cliente."
                });

            } else {
                self.gui.show_popup('selection', {
                    title: "COTIZAR O FACTURAR A CRÉDITO",
                    list: [
                        {label: 'CREAR COTIZACIÓN', item: 0},
                        {label: 'CREAR FACTURA A CRÉDITO', item: 1}
                    ],
                    confirm: function (item) {
                        if (item == 0) {
                            self.gui.show_popup('selection', {
                                title: "CREAR COTIZACIÓN",
                                list: [
                                    {label: 'IMPRIMIR', item: 0},
                                    {label: 'ENVIAR POR CORREO', item: 1}
                                ],
                                confirm: function (item) {
                                    if (item == 0) {
                                        self.create_sale_order("printer")
                                    } else {
                                        if (!client.email) {
                                            self.gui.show_popup('alert', {
                                                title: "CLIENTE SIN CORREO ELECTRONICO",
                                                body: "DEBE AGREGAR UN CORREO ELECTRONICO AL REGISTRO DEL CLIENTE."
                                            });
                                        } else {
                                            self.create_sale_order("email")
                                        }
                                    }
                                }
                            });
                        } else {
                            self.show_credit_popup()
                        }
                    }
                });
            }
        },
        show_credit_popup: function () {
            var self = this;
            var order = self.pos.get('selectedOrder');
            var orderdata = order.export_as_JSON();
            new Model('pos.order').call("get_customer_credit", [orderdata])
                .done(function (res) {
                    if (res.nocredit_limit == true) {
                        self.gui.show_popup('error', {
                            title: "SIN CRÉDITO",
                            body: "EL CLIENTE SELECCIONADO NO TIENE CRÉDITO.",
                        });
                    } else if (res.overdue == true) {
                        self.gui.show_popup('error', {
                            title: "PAGOS PENDIENTES",
                            raw: res.raw
                        });
                    } else if (res.credit_exceeded == true) {
                        self.gui.show_popup('error', {
                            title: "EL LÍMITE DE CRÉDITO SERÁ EXCEDIDO",
                            raw: res.raw
                        });
                    } else {
                        self.gui.show_popup('textinput', {
                            title: "DIGITE EL NÚMERO DE ORDEN DE COMPRA DEL CLIENTE",
                            confirm: function (value) {
                                if (!value) {
                                    alert("PARA FACTURAR DESDE EL POS ES REQUERIDO EL NUMERO DE ORDEN DE COMPRA DEL CLIENTE.");
                                    return;
                                }
                                else {
                                    self.create_credit_invoice(value)
                                }

                            }
                        });
                    }
                })
                .fail(function () {

                });

        },
        create_sale_order: function (option) {
            var self = this;
            var order = self.pos.get('selectedOrder');
            var user = self.pos.cashier || self.pos.user;
            var orderdata = order.export_as_JSON();
            new Model('pos.order').call("create_sale_order", [orderdata, user.id])
                .done(function (res) {
                    self.pos.delete_current_order();
                    if (option == 'printer') {
                        self.print_quotation(res.id)
                    } else if (option == 'email') {
                        self.quotation_send_mail(res)
                    } else {
                        self.create_credit_invoice(res.id, option)
                    }
                })
                .fail(function (res) {
                    self.gui.show_popup('error', {
                        'title': "Error!!!",
                        'body': "Compruebe su conexión a Internet y vuelva a intentarlo."
                    });
                });
        },
        create_credit_invoice: function (option) {
            var self = this;
            var order = self.pos.get('selectedOrder');
            var user = self.pos.cashier || self.pos.user;
            var orderdata = order.export_as_JSON();
            orderdata.nota = option

            new Model('pos.order').call("create_credit_invoice", [orderdata, user.id], undefined, {timeout: 100000})
                .then(function (result) {

                    self.gui.show_popup('selection', {
                        title: "FACTURA CREADA "+result.number,
                        list: [
                            {label: 'IMPRIMIR FACTURA', item: 0}
                        ],
                        confirm: function () {
                            self.chrome.do_action('account.account_invoices', {
                                additional_context: {
                                    active_ids: [result.invoice_id]
                                }
                            });
                        }
                    });
                });
        },
        print_quotation:

            function (order_id) {
                var self = this;
                (new Model('pos.order')).call('wk_print_quotation_report', [])
                    .then(function (result) {
                        this.action_manager = new ActionManager(this);
                        this.action_manager.do_action(result, {
                            additional_context: {
                                active_id: order_id,
                                active_ids: [order_id],
                                active_model: 'sales.order'
                            }
                        });
                        self.gui.show_screen('products');
                    })
                    .fail(function (error, event) {
                        self.gui.show_popup('error', {
                            'title': "Error!!!",
                            'body': "Compruebe su conexión a Internet y vuelva a intentarlo."
                        });
                    });
            }

        ,
        quotation_send_mail: function (result) {
            var self = this;
            (new Model('pos.order')).call('send_email', [result.id])
                .then(function (res) {
                    self.gui.show_popup('alert', {
                        'title': 'Exitoso',
                        'body': 'Se envío el correo electrónico de la cotizacion No.' + result.name,
                        close: function () {
                            self.gui.show_screen('products');
                        }
                    });
                })
                .fail(function (error, event) {
                    self.gui.show_popup('error', {
                        'title': "Error!!!",
                        'body': "Compruebe su conexión a Internet y vuelva a intentarlo."
                    });
                });
        }
        ,
    });

    screens.define_action_button({
        'name': 'SalesOrder',
        'widget': CreateSalesOrderWidget,
        'condition': function () {
            return true;
        }
    });

});