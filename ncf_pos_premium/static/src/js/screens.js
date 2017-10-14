odoo.define('ncf_pos_premium.screens', function (require) {
    "use strict";

    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var Model = require('web.DataModel');
    var gui = require('point_of_sale.gui');
    var formats = require('web.formats');
    var web_data = require('web.data');
    var IpfApi = require('ipf_manager.service');
    var ActionManager1 = require('web.ActionManager');
    var floors = require('pos_restaurant.floors');
    var QWeb = core.qweb;
    var framework = require('web.framework');

    // pos_multi_session_restaurant
    var FloorScreenWidget;
    _.each(gui.Gui.prototype.screen_classes, function (o) {
        if (o.name == 'floors') {
            FloorScreenWidget = o.widget;
            FloorScreenWidget.include({
                start: function () {
                    var self = this;
                    this._super();
                    this.pos.bind('change:orders-count-on-floor-screen', function () {
                        self.renderElement();
                    });
                }
            });
            return false;
        }
    });
    var _t = core._t;

    screens.ReceiptScreenWidget.include({

        ncf_render_receipt: function (fiscal_data) {
            var order = this.pos.get_order();
            order.fiscal_type_name = fiscal_data.fiscal_type_name;
            order.ncf = fiscal_data.ncf;
            order.origin_ncf = fiscal_data.origin;
            this.$('.pos-receipt-container').html(QWeb.render('PosTicket', {
                widget: this,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
            }));
        },
        render_receipt: function () {
            var self = this;
            var order = this.pos.get_order();
            $(".pos-sale-ticket").hide();
            $(".button.next.highlight").hide();
            $(".button.print").hide();

            if (self.pos.config.iface_fiscal_printer === false) {
                new Model('pos.order').call("get_fiscal_data", [order.name]).then(function (fiscal_data) {
                    self.ncf_render_receipt(fiscal_data);
                    $(".pos-sale-ticket").show();
                    $(".button.next.highlight").show();
                    $(".button.print").show();
                });
            }
        },
        print_xml: function () {
            var env = {
                pos: this.pos,
                widget: this,
                order: this.pos.get_order(),
                receipt: this.pos.get_order().export_for_printing(),
                paymentlines: this.pos.get_order().get_paymentlines()
            };
            var receipt = QWeb.render('XmlReceipt', env);

            this.pos.proxy.print_receipt(receipt);
            this.pos.get_order()._printed = true;
        },
    });

    gui.Gui.prototype.screen_classes.filter(function (el) {
        return el.name == 'splitbill'
    })[0].widget.include({
        pay: function (order, neworder, splitlines) {
            this._super(order, neworder, splitlines);
            neworder.save_to_db();
        }
    });

    screens.OrderWidget.include({
        // pos_multi_session
        render_orderline: function (orderline) {
            var self = this;
            var el_str = QWeb.render('Orderline', {widget: this, line: orderline});
            var el_node = document.createElement('div');
            el_node.innerHTML = _.str.trim(el_str);
            el_node = el_node.childNodes[0];
            el_node.orderline = orderline;
            el_node.addEventListener('click', this.line_click_handler);
            var ms_info = el_node.querySelector('.ms_info');
            if (ms_info) {
                ms_info.addEventListener('click', (function () {
                    self.gui.select_user({
                        'security': false,
                        'current_user': self.pos.get_cashier(),
                        'title': _t('Seleccione el vendedor'),
                    }).then(function (user) {
                        orderline.ms_info.created.user.id = user.id;
                        orderline.ms_info.created.user.name = user.name;
                        self.renderElement();
                    });
                }))
            }
            var el_lot_icon = el_node.querySelector('.line-lot-icon');
            if (el_lot_icon) {
                el_lot_icon.addEventListener('click', (function () {
                    this.show_product_lot(orderline);
                }.bind(this)));
            }

            orderline.node = el_node;
            return el_node;
        },
        rerender_orderline: function (order_line) {
            if (order_line.node && order_line.node.parentNode) {
                return this._super(order_line);
            }
        },
        // pos_multi_session | pos_multi_session_restaurant
        remove_orderline: function (order_line) {
            if (this.pos.get_order() && this.pos.get_order().get_orderlines().length === 0) {
                if (order_line.node.parentNode) {
                    return this._super(order_line);
                }
                if (this.pos.get_order() && this.pos.get_order().get_orderlines().length === 0) {
                    return this._super(order_line);
                }
            } else {
                order_line.node.parentNode.removeChild(order_line.node);
            }
        },
        bind_order_events: function () {
            this._super();
            var order = this.pos.get('selectedOrder');
            order.orderlines.bind('add remove', this.chrome.check_allow_delete_order, this.chrome);
        },
        // pos_multi_session | pos_multi_session_restaurant
        update_summary: function () {
            var order = this.pos.get_order();

            if (order) {
                if (!order.get_orderlines().length) {
                    return;
                }
                this._super();
                var total = order ? order.get_total_with_tax() : 0;
                var taxes = order ? total - order.get_total_without_tax() : 0;
                if (order != null && order.is_return_order) {
                    total *= -1;
                    taxes *= -1;
                }

                this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
                this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);

                var buttons = this.getParent().action_buttons;
                if (buttons && buttons.submit_order && this.all_lines_printed(order)) {
                    buttons.submit_order.highlight(false);
                }
            }
        },
        // pos_multi_session | pos_multi_session_restaurant
        all_lines_printed: function (order) {
            var not_printed_line = order.orderlines.find(function (lines) {
                return lines.mp_dirty;
            });
            return !not_printed_line;
        },
    });

    screens.ReceiptScreenWidget.extend({
        // pos_multi_session
        finish_order: function () {
            if (!this._locked) {
                this.pos.get('selectedOrder').destroy({'reason': 'finishOrder'});
            }
        },
        /* since saas-6:
        click_next: function() {
            this.pos.get('selectedOrder').destroy({'reason': 'finishOrder'});
        }
         */
    });

    screens.ProductListWidget.include({
        renderElement: function () {
            this._super();
            var order = this.pos.get_order();

            if (order) {
                if (order.is_return_order) {

                    $('.product').css("pointer-events", "none");
                    $('.product').css("opacity", "0.4");
                    $('#refund_order_notify').show();
                    $('#cancel_refund_order').show();
                    self.$('.numpad-backspace').css("pointer-events", "none");
                }
                else {
                    $('.product').css("pointer-events", "");
                    $('.product').css("opacity", "");
                    $('#refund_order_notify').hide();
                    $('#cancel_refund_order').hide();
                    this.$('.numpad-backspace').css("pointer-events", "");
                }
            }
        }
    });

    screens.ProductScreenWidget.include({
        init: function () {
            this._super.apply(this, arguments);
        },
        show: function () {
            var self = this;

            $("#cancel_refund_order").on("click", function () {
                $(".deleteorder-button").trigger("click");
            });

            this._super();

            this.product_categories_widget.reset_category();

            this.numpad.state.reset();

        },
        start: function () {
            this._super();
            var user = this.pos.cashier || this.pos.user;
            if (!user.allow_payments) {
                this.actionpad.$('.pay').hide();
            }
        },
        renderElement: function () {
            this._super();
            this.pos.bind('change:cashier', this.checkPayAllowed, this);
            this.pos.bind('change:cashier', this.checkCreateOrderLine, this);

            this.$el.find("#pos-options-bar").collapse({
                open: function () {
                    // The context of 'this' is applied to
                    // the collapsed details in a jQuery wrapper
                    this.slideDown(100);
                },
                close: function () {
                    this.slideUp(100);
                },
                accordion: true,
                persist: true
            });
        },
        checkCreateOrderLine: function () {
            var user = this.pos.cashier || this.pos.user;
            if (!user.allow_create_order_line) {
                $('.numpad').hide();
                $('div.product-screen.screen > div.rightpane > table > tbody > tr:nth-child(2)').hide();
            } else {
                $('.numpad').show();
                $('div.product-screen.screen > div.rightpane > table > tbody > tr:nth-child(2)').show();
            }
        },
        checkPayAllowed: function () {
            var user = this.pos.cashier || this.pos.user;
            if (!user.allow_payments) {
                this.actionpad.$('.pay').hide();
            } else {
                this.actionpad.$('.pay').show();
            }
        }
    });

    screens.ScreenWidget.include({
        renderElement: function () {
            this._super();
            var user = this.pos.cashier || this.pos.user;
            if (!user.allow_payments) {
                $('.pay').hide();
            } else {
                $('.pay').show();
            }
            if (!user.allow_create_order_line) {

                $('.numpad').hide();
                $('div.product-screen.screen > div.rightpane > table > tbody > tr:nth-child(2)').hide();
            } else {
                $('.numpad').show();
                $('div.product-screen.screen > div.rightpane > table > tbody > tr:nth-child(2)').show();
            }
        }
    });

    screens.ActionpadWidget.include({
        renderElement: function () {
            this._super();
            var self = this;


            this.$('.pay').bind("click", function () {
                var client = self.pos.get_order().get_client();

                if (client == null) {
                    alert("Debe de configurar un cliente por defecto en el PTV.")
                    return
                }

                if (client.sale_fiscal_type !== 'final' && (client.vat === false || client.vat === null)) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Para el tipo de comprobante',
                        'body': 'No puede crear una factura con crédito fiscal si el cliente no tiene RNC o Cédula. Puede pedir ayuda para que el cliente sea registrado correctamente si este desea comprobante fiscal',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                }

                if (self.pos.get_order().orderlines.models.length === 0) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Facntura sin productos',
                        'body': 'No puede pagar un ticket sin productos',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                }


                var valid_product_lines = _.every(self.pos.get_order().orderlines.models, function (line) {
                    return line.get_price_with_tax() !== 0;
                });

                if (!valid_product_lines) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Prodcuto valor 0',
                        'body': 'Favor revisar el ticket, hay productos valor 0.',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                }
            });

            var user = self.pos.cashier || this.pos.user;

            if (!user.allow_payments) {
                $('.pay').hide();
            } else {
                $('.pay').show();
            }
        }
    });

    screens.NumpadWidget.include({
        init: function () {
            this._super.apply(this, arguments);
            this.pos.bind('change:cashier', this.check_access, this);
        },
        start: function () {
            this._super();
            var self = this;
            this.pos.keypad.set_action_callback(function (data) {
                self.keypad_action(data, self.pos.keypad.type);
            });
        },
        renderElement: function () {
            this._super();
            this.check_access();
        },
        check_access: function () {
            var user = this.pos.cashier || this.pos.user;
            if (!user.allow_discount) {
                this.$el.find("[data-mode='discount']").css('visibility', 'hidden');
            } else {
                this.$el.find("[data-mode='discount']").css('visibility', 'visible');
            }
            if (!user.allow_edit_price) {
                this.$el.find("[data-mode='price']").css('visibility', 'hidden');
            } else {
                this.$el.find("[data-mode='price']").css('visibility', 'visible');
            }
        },
        clickAppendNewChar: function (event) {
            var self = this;
            if (!self.pos.get_order().is_return_order)
                this._super(event);
        },
        clickSwitchSign: function () {
            var self = this;

            if (!self.pos.get_order().is_return_order)
                this._super(event);
        },
        clickDeleteLastChar: function () {
            var user = this.pos.cashier || this.pos.user;
            if (!user.allow_decrease_amount && this.state.get('mode') === 'quantity') {
                return;
            }
            if (!user.allow_delete_order_line && this.state.get('buffer') === "" && this.state.get('mode') === 'quantity') {
                return;
            }
            return this._super();
        },
        keypad_action: function (data, type) {
            if (data.type === type.numchar) {
                this.state.appendNewChar(data.val);
            }
            else if (data.type === type.bmode) {
                this.state.changeMode(data.val);
            }
            else if (data.type === type.sign) {
                this.clickSwitchSign();
            }
            else if (data.type === type.backspace) {
                this.clickDeleteLastChar();
            }
        }
    });

    screens.ClientListScreenWidget.include({
        show: function () {
            var self = this;
            self._super();

            $('.view_all_order').on('click', function () {
                if (this.id) {
                    self.gui.show_screen('wk_order', {
                        'customer_id': this.id
                    });
                }
            });

            if (self.pos.get_order().is_return_order) {
                self.gui.back();
            }
        },
        save_client_details: function (partner) {
            framework.blockUI();
            this._super(partner)
            framework.unblockUI();
        },
        save_changes: function () {
            var self = this;
            var order = this.pos.get_order();
            if (this.has_client_changed()) {
                if (this.new_client) {

                    if (self.new_client.property_account_position_id != null) {
                        order.fiscal_position = _.find(this.pos.fiscal_positions, function (fp) {
                            return fp.id === self.new_client.property_account_position_id[0];
                        });

                    } else {
                        order.fiscal_position = undefined;
                    }

                } else {
                    order.fiscal_position = undefined;
                }

                order.set_client(this.new_client);
            }
        }
    });

    screens.PaymentScreenWidget.include({
        show: function () {
            var self = this;
            self._super();


            $('#order_note').on('focus', function () {
                window.document.body.removeEventListener('keypress', self.keyboard_handler);
                window.document.body.removeEventListener('keydown', self.keyboard_keydown_handler);
            });

            $('#order_note').on('focusout', function () {
                window.document.body.addEventListener('keypress', self.keyboard_handler);
                window.document.body.addEventListener('keydown', self.keyboard_keydown_handler);
            });
            this.pos.keypad.disconnect();

        },
        hide: function () {
            this._super();
            this.pos.keypad.connect();
        },
        payment_input: function (input) {
            var newbuf = this.gui.numpad_input(this.inputbuffer, input, {'firstinput': this.firstinput});

            this.firstinput = (newbuf.length === 0);
            if (this.gui.has_popup()) {
                return;
            }

            if (newbuf !== this.inputbuffer) {
                this.inputbuffer = newbuf;
                var order = this.pos.get_order();
                if (order.selected_paymentline) {
                    var amount = this.inputbuffer;

                    if (this.inputbuffer !== "-") {
                        amount = formats.parse_value(this.inputbuffer, {type: "float"}, 0.0);
                    }
                    var due_amount = parseFloat(this.$('.paymentline.selected .col-due').text().replace(',', ''));
                    if (amount > due_amount && order.is_return_order) {
                        this.inputbuffer = due_amount.toString();
                        order.selected_paymentline.set_amount(due_amount);
                        this.order_changes();
                        this.render_paymentlines();
                        this.$('.paymentline.selected .edit').text(this.format_currency_no_symbol(due_amount));
                    }
                    else {
                        order.selected_paymentline.set_amount(amount);
                        this.order_changes();
                        this.render_paymentlines();
                        this.$('.paymentline.selected .edit').text(this.format_currency_no_symbol(amount));
                    }
                }
            }
        },
        order_is_valid: function (force_validation) {
            var order = this.pos.get_order();

            if (!order.get_client()) {
                alert()
            }

            if (order.is_return_order) {
                return true
            } else {
                return this._super(force_validation)
            }

        },
        validate_order: function (options) {
            var currentOrder = this.pos.get_order();

            if (!currentOrder.get_client()) {
                this.gui.show_popup('error', {
                    'title': 'Por favor indique una empresa para la venta.',
                    'body': 'Tambien se puede configurar un cliente por defecto en la confguracion del PTV.'
                });
                return;
            } else if (currentOrder.get_orderlines().length === 0) {
                this.gui.show_popup('error', {
                    'title': 'Empty Order',
                    'body': 'There must be at least one product in your order before it can be validated.'
                });
                return;
            }

            this._super(options);
        },
        click_paymentmethods: function (id) {
            var self = this;

            var cashregister = null;
            for (var i = 0; i < this.pos.cashregisters.length; i++) {
                if (this.pos.cashregisters[i].journal_id[0] === id) {
                    cashregister = this.pos.cashregisters[i];
                    break;
                }
            }
            var order = self.pos.get_order();


            if (cashregister.journal.credit && !order.is_return_order) {

                self.gui.show_popup('payment_screen_text_input', {
                    title: "Digite el número de NCF de la nota de crédito",
                    confirm: function (input) {

                        var credit_error = false;

                        var order_paymentlines = order.get_paymentlines();
                        _.each(order_paymentlines, function (paymentline) {
                            if (paymentline.payment_reference === input) {
                                credit_error = true;
                                self.gui.show_popup('error', {
                                    title: "Ya esta nota de crédito esta aplicada",
                                    body: input
                                })
                            }
                        });

                        if (input === "") {
                            credit_error = true;
                            self.gui.show_popup('error', {
                                title: "EL NCF NO ES VALIDO.",
                                body: input
                            })
                        }

                        if (credit_error) {
                            return
                        }

                        return new Model('pos.order').call("get_credit_by_ncf", [input])
                            .then(function (result) {

                                if (!result) {
                                    self.gui.show_popup('error', {
                                        title: "EL NCF NO ES VALIDO.",
                                        body: input
                                    })
                                } else if (result.partner_id != order.get_client().id) {
                                    self.gui.show_popup('error', {
                                        title: "Cliente no pertenece a la Nota de Crédito",
                                        body: "Para aplicar una nota de crédito el ticket debe tener el mismo cliente de la nota de crédito."
                                    })
                                }
                                else {
                                    cashregister.payment_reference = input;
                                    cashregister.credit_amount = result.residual_amount;
                                    self.pos.get_order().add_paymentline(cashregister);
                                    self.reset_input();
                                    self.render_paymentlines();
                                }
                            });
                    }
                });
            } else if (cashregister.journal.type == "bank" && !cashregister.journal.credit) {
                self.gui.show_popup('payment_screen_text_input', {
                    title: "Digite un número de referencia.",
                    confirm: function (input) {
                        cashregister.payment_reference = input;
                        self.pos.get_order().add_paymentline(cashregister);
                        self.reset_input();
                        self.render_paymentlines();
                    }
                });

            } else {
                this.pos.get_order().add_paymentline(cashregister);
                this.reset_input();
                this.render_paymentlines();
            }
        }
    });

    var OrdersScreenWidget = screens.ScreenWidget.extend({
        template: 'OrdersScreenWidget',
        init: function (parent, options) {
            this._super(parent, options);
        },
        show: function () {
            var self = this;
            this._super();

            var orders = self.pos.db.pos_all_orders;
            this.render_list(orders, undefined);

            this.$('.order_search').keyup(function (e) {
                var token = e.keyCode;
                if (token == 13) {
                    self.render_list(orders, this.value);
                }
            });

            this.$('.search_action_button').click(function () {
                self.render_list(orders, self.$('.order_search').val());
            });


            this.$('.back').on('click', function () {
                self.gui.show_screen('products');
            });

            this.details_visible = false;
            this.selected_tr_element = null;

            self.$('.wk-order-list-contents').delegate('.wk-order-line', 'click', function (event) {
                self.line_select(event, $(this), parseInt($(this).data('id')));
            });

            var contents = this.$('.order-details-contents');
            contents.empty();
            var parent = self.$('.wk_order_list').parent();
            parent.scrollTop(0);

            //reorder
            this.$('.wk-order-list-contents').delegate('.wk_reorder_content', 'click', function (event) {
                var order_line_data = self.pos.db.pos_all_order_lines;
                var order = self.pos.get_order();
                for (var i = 0; i < order_line_data.length; i++) {
                    if (order_line_data[i].order_id[0] == this.id) {
                        var product = self.pos.db.get_product_by_id(order_line_data[i].product_id[0]);
                        order.add_product(product, {quantity: order_line_data[i].qty});
                    }
                }
                self.gui.show_screen('products');
            });

            //reprint
            this.$('.wk-order-list-contents').delegate('.wk_reprint_content', 'click', function (event) {

                var order_data = self.pos.db.pos_all_orders;
                for (var i = 0; i < order_data.length; i++) {
                    if (order_data[i].id == this.id) {
                        var order_to_reprint = order_data[i];
                    }
                }
                self.gui.show_popup('selection', {
                    title: "¿Como desea reimprimir la factura?",
                    list: [
                        {label: 'Impresora PTV', item: "pos"},
                        {label: 'Descargar PDF', item: "pdf"},
                        {label: 'Enviar por correo', item: "email"}
                    ],
                    confirm: function (item) {

                        if (item === "pos") {
                            return new Model('pos.order').call("get_invoice_id_from_pos_order_id", [order_to_reprint.id])
                                .then(function (invoice_id) {
                                    if (invoice_id) {
                                        if (self.pos.config.iface_fiscal_printer) {
                                            var context = new web_data.CompoundContext({
                                                active_model: "account.invoice",
                                                active_id: invoice_id
                                            });
                                            var ipfProxy = new IpfApi();
                                            ipfProxy.post_invoice(context);

                                        } else {
                                            alert("Esta funcionalidad solo funciona con la impresora fiscal.")
                                            return
                                        }


                                        self.gui.show_screen('products');
                                    }
                                });
                        }
                        else if (item === "pdf") {
                            return new Model('pos.order').call("get_invoice_id_from_pos_order_id", [order_to_reprint.id])
                                .then(function (invoice_id) {
                                    if (invoice_id) {

                                        this.action_manager = new ActionManager1(this);
                                        this.action_manager.do_action(178, {
                                            additional_context: {
                                                active_id: invoice_id,
                                                active_ids: [invoice_id],
                                                active_model: 'account.invoice'
                                            }
                                        });
                                        self.gui.show_screen('products');

                                    }
                                });
                        }
                        else if (item === "email") {
                            new Model('pos.order').call("get_email_from_pos", [order_to_reprint.partner_id[0]])
                                .then(function (result) {
                                    self.gui.show_popup('textinput', {
                                        title: "Enviar factura por Email.",
                                        value: result,
                                        confirm: function (result) {
                                            if (result) {
                                                self.mail_invoice_from_pos(order_to_reprint.id, result);
                                                self.gui.show_screen('products');
                                            }
                                        },
                                        cancel: function () {

                                        }
                                    });
                                });
                        }

                    },
                    cancel: function () {
                        // user chose nothing
                    }
                });
            });


        },
        get_customer: function (customer_id) {
            var self = this;
            if (self.gui)
                return self.gui.get_current_screen_param('customer_id');
            else
                return undefined;
        },
        search_order: function (order, input_txt) {
            var customer_id = this.get_customer();
            var new_order_data = [];
            if (customer_id != undefined) {
                for (var i = 0; i < order.length; i++) {
                    if (order[i].partner_id[0] == customer_id)
                        new_order_data = new_order_data.concat(order[i]);
                }
                order = new_order_data;
            }

            if (input_txt != undefined && input_txt != '') {
                var new_order_data = [];
                var search_text = input_txt.toLowerCase();
                for (var i = 0; i < order.length; i++) {
                    if (order[i].partner_id == '') {
                        order[i].partner_id = [0, '-'];
                    }


                    try {
                        var invoice_id = ((order[i].invoice_id[1].toLowerCase()).indexOf(search_text) != -1)
                    } catch (error) {
                        var invoice_id = "";
                    }

                    if (invoice_id || ((order[i].name.toLowerCase()).indexOf(search_text) != -1) || ((order[i].partner_id[1].toLowerCase()).indexOf(search_text) != -1)) {
                        new_order_data = new_order_data.concat(order[i]);
                    }
                }
                order = new_order_data;
            }

            return order;

        },
        render_list: function (order, input_txt) {
            var self = this;

            var wk_orders = self.search_order(order, input_txt);

            if (wk_orders.length === 0) {

                if (input_txt != undefined) {
                    framework.blockUI();
                    var PosOrder = new Model('pos.order');
                    PosOrder.call("order_search_from_ui", [input_txt])
                        .then(function (orders) {

                            self.pos.db.pos_all_orders = orders.wk_order;
                            self.pos.db.order_by_id = {};
                            orders.wk_order.forEach(function (order) {
                                self.pos.db.order_by_id[order.id] = order;
                            });

                            self.pos.db.pos_all_order_lines = orders.wk_order_lines;
                            self.pos.db.line_by_id = {};
                            orders.wk_order_lines.forEach(function (line) {
                                self.pos.db.line_by_id[line.id] = line;
                            });

                        }).then(function () {
                        var pos_all_orders = self.pos.db.pos_all_orders;
                        wk_orders = self.search_order(pos_all_orders, input_txt);
                        var contents = self.$el[0].querySelector('.wk-order-list-contents');
                        contents.innerHTML = "";
                        for (var i = 0, len = Math.min(wk_orders.length, 1000); i < len; i++) {
                            var orderline_html = QWeb.render('WkOrderLine', {
                                widget: this,
                                order: wk_orders[i],
                                customer_id: wk_orders[i].partner_id[0],
                            });
                            var orderline = document.createElement('tbody');
                            orderline.innerHTML = orderline_html;
                            orderline = orderline.childNodes[1];
                            contents.appendChild(orderline);
                        }
                    }).done(function () {
                        framework.unblockUI();
                    })
                }

            } else {

                var contents = this.$el[0].querySelector('.wk-order-list-contents');
                contents.innerHTML = "";

                for (var i = 0, len = Math.min(wk_orders.length, 1000); i < len; i++) {
                    var orderline_html = QWeb.render('WkOrderLine', {
                        widget: this,
                        order: wk_orders[i],
                        customer_id: wk_orders[i].partner_id[0],
                    });
                    var orderline = document.createElement('tbody');
                    orderline.innerHTML = orderline_html;
                    orderline = orderline.childNodes[1];
                    contents.appendChild(orderline);
                }
            }

        },
        close: function () {
            this._super();
            this.$('.wk-order-list-contents').undelegate();
        },
        mail_invoice_from_pos: function (order_id, email) {
            var self = this;
            return new Model('pos.order').call("mail_invoice_from_pos", [order_id, email])
                .then(function (result) {
                    if (result) {
                        self.gui.show_popup('alert', {
                            title: "Informacion!",
                            body: "La factura se envió correctamente.!"
                        });
                    } else {
                        self.gui.show_popup('error', {
                            title: "Alerta!",
                            body: "Falló el envío de la factura por email verifique si está correcto."
                        });
                    }

                })
                .fail(function (error, event) {
                    self.gui.show_popup('error', {
                        'title': "Error!!!",
                        'body': "Compruebe su conexión a Internet y vuelva a intentarlo.",
                    });
                });

        },
        line_select: function (event, $line, id) {
            var self = this;
            var order = self.pos.db.order_by_id[id];
            this.$('.wk_order_list .lowlight').removeClass('lowlight');
            if ($line.hasClass('highlight')) {
                $line.removeClass('highlight');
                $line.addClass('lowlight');
                this.display_order_details('hide', order);
            } else {
                this.$('.wk_order_list .highlight').removeClass('highlight');
                $line.addClass('highlight');
                self.selected_tr_element = $line;
                var y = event.pageY - $line.parent().offset().top;
                self.display_order_details('show', order, y);
            }
        },
        display_order_details: function (visibility, order, clickpos) {
            var self = this;
            var contents = this.$('.order-details-contents');
            var parent = this.$('.wk_order_list').parent();
            var scroll = parent.scrollTop();
            var height = contents.height();
            var orderlines = [];
            var statements = [];
            var journal_ids_used = [];
            if (visibility === 'show') {
                order.lines.forEach(function (line_id) {
                    orderlines.push(self.pos.db.line_by_id[line_id]);
                });
                order.statement_ids.forEach(function (statement_id) {
                    var statement = self.pos.db.statement_by_id[statement_id];
                    statements.push(statement);
                    journal_ids_used.push(statement.journal_id[0]);
                });
                contents.empty();
                contents.append($(QWeb.render('OrderDetails', {
                    widget: this,
                    order: order,
                    orderlines: orderlines,
                    statements: statements
                })));
                var new_height = contents.height();
                if (!this.details_visible) {
                    if (clickpos < scroll + new_height + 20) {
                        parent.scrollTop(clickpos - 20);
                    } else {
                        parent.scrollTop(parent.scrollTop() + new_height);
                    }
                } else {
                    parent.scrollTop(parent.scrollTop() - height + new_height);
                }
                this.details_visible = true;
                self.$("#close_order_details").on("click", function () {
                    self.selected_tr_element.removeClass('highlight');
                    self.selected_tr_element.addClass('lowlight');
                    self.details_visible = false;
                    self.display_order_details('hide', null);
                });
                self.$("#wk_refund").on("click", function () {
                    // var order_list = self.pos.db.pos_all_orders;
                    // var order_line_data = self.pos.db.pos_all_order_lines;
                    // var order_id = this.id;
                    var message = '';
                    var non_returnable_products = false;
                    var original_orderlines = [];
                    var allow_return = true;


                    if (order.return_status == 'Fully-Returned') {
                        message = 'Lo sentimos, no puede devolver el mismo pedido dos veces !!'
                        allow_return = false;
                    }
                    if (allow_return) {
                        order.lines.forEach(function (line_id) {
                            var line = self.pos.db.line_by_id[line_id];
                            var product = self.pos.db.get_product_by_id(line.product_id[0]);
                            if (product.not_returnable) {
                                non_returnable_products = true;
                                message = 'Este pedido contiene algunos productos no retornables, ¿desea devolver otros productos?'
                            }
                            else if (line.qty - line.line_qty_returned > 0)
                                original_orderlines.push(line);
                        });
                        if (original_orderlines.length == 0) {
                            self.gui.show_popup('my_message', {
                                'title': '¡No puede devolver esta orden !!!',
                                'body': "¡No hay productos retornables para esta orden!",
                            });
                        }
                        else if (non_returnable_products) {
                            self.gui.show_popup('confirm', {
                                'title': 'Warning !!!',
                                'body': message,
                                confirm: function () {
                                    self.gui.show_popup('return_products_popup', {
                                        'orderlines': original_orderlines,
                                        'order': order,
                                        'is_partial_return': true,
                                    });
                                },
                            });
                        }
                        else {
                            self.gui.show_popup('return_products_popup', {
                                'orderlines': original_orderlines,
                                'order': order,
                                'is_partial_return': false,
                            });
                        }
                    }
                    else {
                        self.gui.show_popup('my_message', {
                            'title': 'Error!!!',
                            'body': message,
                        });
                    }
                });
            }
            if (visibility === 'hide') {
                contents.empty();
                if (height > scroll) {
                    contents.css({height: height + 'px'});
                    contents.animate({height: 0}, 400, function () {
                        contents.css({height: ''});
                    });
                } else {
                    parent.scrollTop(parent.scrollTop() - height);
                }
                this.details_visible = false;
            }
        }
    });

    gui.define_screen({name: 'wk_order', widget: OrdersScreenWidget});


    var AllOrder = screens.ActionButtonWidget.extend({
        template: 'all_orders_action_button',
        button_click: function () {
            this.gui.show_screen('wk_order', {});
        }
    });

    screens.define_action_button({
        'name': 'all_orders_action',
        'widget': AllOrder,
        'condition': function () {
            return true;
        },
    });


    return OrdersScreenWidget;

});