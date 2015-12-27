Date.prototype.toDateInputValue = (function() {
    var localtz = new Date(this);
    localtz.setMinutes(this.getMinutes() - this.getTimezoneOffset());
    return localtz.toJSON().slice(0, 10);
});

checkBrowserCompatibility = function(){
    if(!$.browser.chrome) {
        bootbox.alert("Las funciones de la impresora fiscal solo funciona con google Chrome! y con el plugin <a target='_blank' href='https://chrome.google.com/webstore/detail/allow-marcos-ipf-print/pnjmkefgjdhmoepnlmpnkdgjpbooolba?utm_source=gmail'>Allow-Marcos-IPF-Print</a>")
        return false
    } else {
        return true
    }
};

openerp.ipf_manager = function (instance, local) {
    var _t = openerp.web._t,
        _lt = openerp.web._lt;
    var QWeb = openerp.web.qweb;

    local.ipfAPI = instance.Widget.extend({

        init: function () {
            this._super();
            this.host;
            this.response;
            this.showDialogOnget_printer_information = true;
            this.serial;
        },
        get_host: function (context) {
            var self = this;
            this.host = null;
            return new openerp.web.Model("ipf.printer.config").call("get_ipf_host", [], {"context": context}).then(function (data) {
                self.host = data.host;
            });
        },
        get_software_version: function (context) {
            var self = this;
            self.get_host(context).then(function () {
                var url = self.host + "/software_version";
                return self.get_report(url, "GET", "get_software_version");
            });
        },
        get_state: function (context) {
            var self = this;
            self.get_host(context).then(function () {
                var url = self.host + "/state";
                return self.get_report(url, "GET", "get_state");
            });
        },
        get_printer_information: function (context) {
            var self = this;
            self.get_host(context).then(function () {
                var url = self.host + "/printer_information";
                return self.get_report(url, "GET", "get_printer_information", context, null);
            });
        },
        get_advance_paper: function (context) {
            var self = this;
            self.get_host(context).then(function () {
                var url = self.host + "/advance_paper";
                return self.get_report(url, "GET", "get_advance_paper");
            });
        },
        get_advance_paper_number: function (context, number) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/advance_paper/" + number;
                return self.get_report(url, "GET", "post_advance_paper_number");
            });
        },
        get_cut_paper: function (context) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/cut_paper";
                return self.get_report(url, "GET", "get_cut_paper");
            });
        },
        get_z_close: function (context) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/zclose";
                return self.get_report(url, "GET", "get_z_close");
            });
        },
        get_z_close_print: function (context) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/zclose/print";
                return self.get_report(url, "GET", "get_z_close_print");
            });
        },
        get_new_shift: function (context) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/new_shift";
                return self.get_report(url, "GET", "get_new_shift");
            });
        },
        get_new_shift_print: function (context) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/new_shift/print";
                return self.get_report(url, "GET", "get_new_shift_print");
            });
        },
        get_x: function (context) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/X";
                return self.get_report(url, "GET", "get_x");
            });
        },
        get_information_day: function (context) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/information/day";
                return self.get_report(url, "GET", "get_information_day");
            });
        },
        get_information_shift: function (context) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/information/shift";
                return self.get_report(url, "GET", "get_information_shift");
            });
        },
        get_document_header: function (context) {
            var self = this;
            self.get_host(context).then(function (context) {
                var url = self.host + "/document_header";
                return self.get_report(url, "GET", "get_document_header");
            });
        },
        post_document_header: function (context, data) {
            var self = this;
            self.get_host(context).then(function (result) {
                var url = self.host + "/document_header";
                return self.get_report(url, "POST", "post_document_header", context, data);
            });
        },
        get_daily_book: function (context, bookday) {
            var self = this;

            self.get_host(context).then(function (result) {
                $.ajax({
                    "type": "GET",
                    "url": self.host+"/printer_information"
                }).done(function(response){
                    var aplitBookDay = bookday.split("-");
                    var serial = JSON.parse(response).response.serial;
                    var url = self.host + "/daily_book/"+serial+"/"+aplitBookDay[2]+"/"+aplitBookDay[1]+"/"+aplitBookDay[0];
                    self.get_book(url, serial, bookday, context);
                }).fail(function(response){
                    console.log(response);
                    var res = false;

                    if (response.responseText) {
                        console.log(JSON.parse(response.responseText));
                        var res = JSON.parse(response.responseText);
                    }

                    if (res) {
                        self.showDialog(res.message)
                    } else
                    if (response.statusText === "error") {
                        self.showDialog("Error de conexion", "El sistema no pudo conectarse a la impresora verifique las conexiones.")
                    }
                });
            })
        },
        post_invoice: function (context) {
            var self = this;
            return self.create_invoice(context);

        },
        get_report: function (url, type, from, context, data) {
            var self = this;
            if (data) {
                var params = {"type": type, "url": url, "data": JSON.stringify(data)}
            } else {
                var params = {"type": type, "url": url}
            }
            
            return $.ajax(params)
                .done(function (response) {
                    console.log(JSON.parse(response));
                    self.show_response(from, JSON.parse(response), context);
                    
                })
                .fail(function (response) {
                    console.log(response);
                    var res = false;

                    if (response.responseText) {
                        console.log(JSON.parse(response.responseText));
                        var res = JSON.parse(response.responseText);
                    }

                    if (res.message === "Fiscal journey not open, try printing at least one invoice." && res) {
                        self.showDialog("Cierre Z", "No hay cierre Z abierto, intente hacer al menos una factura.")
                    } else
                    if (response.statusText === "error") {
                        self.showDialog("Error de conexion", "El sistema no pudo conectarse a la impresora verifique las conexiones.")
                    }
                    
                });
        },
        show_response: function (from, response, context) {
            var self = this;

            if (from === "get_software_version") {
                self.showDialog("Infomación del software", "<strong>Nombre:</strong> " + response.response.name + "</br> <strong>Version:</strong> " + response.response.version)
            } else
            if (from === "get_state") {
                var stateTable = "";
                stateTable += "<table class=\"tg table table-hover table-striped\">";
                stateTable += "  <tr>";
                stateTable += "    <th class=\"tg-47zg\">Estatus Fiscal<\/th>";
                stateTable += "    <th class=\"tg-031e\"><\/th>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">Document<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.document + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">Memory<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.memory + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">Mode<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.mode + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">SubState<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.substate + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">TechMode<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.techmode + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">Open<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.open + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-qjik\"><strong>Estatus del printer<\/strong><\/td>";
                stateTable += "    <td class=\"tg-031e\"><\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">Cover<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.cover + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">Errors<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.errors + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">MoneyBox<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.moneybox + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">Printer<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.printer + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "  <tr>";
                stateTable += "    <td class=\"tg-031e\">State<\/td>";
                stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.state + "<\/td>";
                stateTable += "  <\/tr>";
                stateTable += "<\/table>";
                self.showDialog("Estado de la impresora", stateTable)
            } else
            if (from === "get_printer_information") {
                bootbox.dialog({
                    title: "Infomación del printer",
                    message: "<strong>ID:</strong> " + response.response.id + "</br> <strong>Serial:</strong> " + response.response.serial
                });
            } else
            if (from === "get_advance_paper") {

            } else
            if (from === "post_advance_paper_number") {

            } else
            if (from === "get_cut_paper") {

            } else
            if (from === "get_z_close") {
                bootbox.dialog({
                    title: "Cierre Z",
                    message: "El cierre Z #<strong>"+response.response.znumber+"</strong> se realizo satisfactoriamente"
                });
            } else
            if (from === "get_z_close_print") {
            } else
            if (from === "get_new_shift") {

            } else
            if (from === "get_new_shift_print") {

            } else
            if (from === "get_x") {

            } else
            if (from === "get_information_day") {

                var tableInformation = "";
                tableInformation += "<table class=\"tg table table-hover table-striped\">";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Fecha de inicio<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.init_date + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Hora de inicio<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.init_time + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Número del último cierre Z<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.last_znumber + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos de venta<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.invoices + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos no fiscales o precuentas<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.documents + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos cancelados<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.cancelled + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">NIF inicial<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.first_nif + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">NIF final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.last_nif + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de facturas para consumidor final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de facturas para consumidor final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_itbis + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de facturas fiscales<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de facturas fiscales<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_itbis + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total notas de crédito para consumidor final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_note + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de notas de crédito para consumidor final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_note_itbis + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total nota de crédito con crédito fiscal<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_note + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de nota de crédito con crédito fiscal<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_note_itbis + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total pagado<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_paid + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "<\/table>";


                self.showDialog("Información de día.", tableInformation)

            } else
            if (from === "get_information_shift") {
                var tableInformation = "";
                tableInformation += "<table class=\"tg table table-hover table-striped\">";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Fecha de inicio<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.init_date + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Hora de inicio<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.init_time + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Número del último cierre Z<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.last_znumber + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos de venta<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.invoices + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos no fiscales o precuentas<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.documents + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos cancelados<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.cancelled + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">NIF inicial<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.first_nif + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">NIF final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.last_nif + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de facturas para consumidor final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de facturas para consumidor final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_itbis + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de facturas fiscales<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de facturas fiscales<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_itbis + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total notas de crédito para consumidor final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_note + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de notas de crédito para consumidor final<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_note_itbis + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total nota de crédito con crédito fiscal<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_note + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de nota de crédito con crédito fiscal<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_note_itbis + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "  <tr>";
                tableInformation += "    <td class=\"tg-031e\">Total pagado<\/td>";
                tableInformation += "    <td class=\"tg-031e\">" + response.response.total_paid + "<\/td>";
                tableInformation += "  <\/tr>";
                tableInformation += "<\/table>";


                self.showDialog("Información del turno.", tableInformation)
            }
            if (from === "get_document_header") {
                self.showDialog("Infomación de cabezera", "<h3>" + response.response.text + "</h3>")
            } else
            if (from === "pos_document_header") {

            } else
            if (from === "get_daily_book") {
                self.save_book(response, context)
            }
        },
        showDialog: function (title, message) {
            bootbox.dialog({
                title: title,
                message: message
            });
        },
        get_book: function(url, serial, bookday, context){
            var self = this;
            openerp.web.blockUI();
            $.ajax({
                url: url,
                type: "GET",
                contentType: "text/plain"
            }).done(function (response) {
                self.save_book(response, serial, bookday, context);
                
            }).fail(function(response){
                openerp.web.unblockUI()
                console.log(response);
                    var res = false;

                    if (response.responseText) {
                        console.log(JSON.parse(response.responseText));
                        var res = JSON.parse(response.responseText);
                    }

                    if (res) {
                        self.showDialog(res.message)
                    } else
                    if (response.statusText === "error") {
                        self.showDialog("Error de conexion", "El sistema no pudo conectarse a la impresora verifique las conexiones.")
                    }
                
            });
        },
        save_book: function(response, serial, bookday, context){
            var self = this;
            if (response) {
                return new openerp.web.Model("ipf.printer.config").call("save_book", [response, serial, bookday], {context: context})
                .then(function (data) {
                    if (data) {
                        self.showDialog("Extracción libro diario", "El libro de diario fue generado satisfactoriamente.");
                    }
                }).then(function(){
                        openerp.web.unblockUI()
                    });
            } else {
                openerp.web.unblockUI()
                self.showDialog("Extraccion libro diario", "No hay datos disponibles para esta fecha.");
            }
        },
        create_invoice: function(context){
            var self = this;
            console.log("create_invoice");
            return new openerp.web.Model("ipf.printer.config").call("ipf_print", [], {context: context})
                .then(function (data) {
                    return self.print_receipt(data, context)
                });

        },
        print_receipt: function (data, context) {
            console.log("print_receipt");
            console.log(data);
            var self = this;
            
            $.ajax({
                type: 'POST',
                url: data.host + "/invoice",
                data: JSON.stringify(data)
            })
                .done(function (response) {
                    console.log(response);
                    responseobj = JSON.parse(response);
                    self.nif = responseobj.response.nif;
                    self.print_done(context, data.invoice_id, responseobj.response.nif);
                    
                })
                .fail(function (response) {
                    console.log(response);
                    var res = false;

                    if (response.responseText) {
                        console.log(JSON.parse(response.responseText));
                        res = JSON.parse(response.responseText) || false;
                    }

                    if (res) {
                        self.showDialog(res.message)
                    } else
                    if (response.statusText === "error") {
                        self.showDialog("Error de conexion", "El sistema no pudo conectarse a la impresora verifique las conexiones.")
                    }
                });
        },
        print_done: function (context, invoice_id, nif) {
            var self = this;
            console.log("print_done");
            return new openerp.web.Model("ipf.printer.config").call("print_done", [[invoice_id, nif]], {context: context})
                .then(function (response) {
                    return response;
                })
        }
    });

    local.IpfsoftwareVersion = instance.web.form.FormWidget.extend({
        events: {
            "click #get_software_version": "get_software_version"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_software_version' class='oe_stat_button btn btn-default'><div class='stat_button_icon fa fa-info fa-fw'></div><div>Infomación del <br> software</div></button>");
        },
        get_software_version: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_software_version(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_softwareVersion", "instance.ipf_manager.IpfsoftwareVersion");

    local.Ipfstate = instance.web.form.FormWidget.extend({
        events: {
            "click #get_state": "get_state"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_state' class='oe_stat_button btn btn-default'><div class='stat_button_icon fa fa-life-ring fa-fw'></div><div>Estado</div></button>");
        },

        get_state: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_state(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_state", "instance.ipf_manager.Ipfstate");

    local.IpfPrinterInformation = instance.web.form.FormWidget.extend({
        events: {
            "click #get_printer_information": "get_printer_information"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_printer_information' class='oe_stat_button btn btn-default'><div class='stat_button_icon fa fa-info-circle fa-fw'></div><div>Infomación del <br> printer</div></button>");
        },

        get_printer_information: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_printer_information(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_printer_information", "instance.ipf_manager.IpfPrinterInformation");

    local.IpfPrinterAdvancePaper = instance.web.form.FormWidget.extend({
        events: {
            "click #get_advance_paper": "get_advance_paper"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_advance_paper' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-level-up'></div><div>Sacar papel</div></button>");
        },

        get_advance_paper: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_advance_paper(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_advance_paper", "instance.ipf_manager.IpfPrinterAdvancePaper");

    local.IpfPrinterAdvancePaperNumber = instance.web.form.FormWidget.extend({
        events: {
            "click #get_advance_paper_number": "get_advance_paper_number"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_advance_paper_number' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-sort-numeric-asc'></div><div>Sacar papel No. lineas</div></button>");
        },

        get_advance_paper_number: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            bootbox.prompt({
                title: "Sacar papel introdizca el numero de linas.",
                value: 10,
                callback: function (result) {
                    if (result === null) {
                        return
                    } else {
                        var context = new instance.web.CompoundContext({
                            active_model: self.field_manager.model,
                            active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
                        });
                        var command = new local.ipfAPI();
                        command.get_advance_paper_number(context, result);
                    }
                }
            });

        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_advance_pape_number", "instance.ipf_manager.IpfPrinterAdvancePaperNumber");

    local.IpfPrinterCutPaper = instance.web.form.FormWidget.extend({
        events: {
            "click #get_cut_paper": "get_cut_paper"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_cut_paper' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-scissors'></div><div>Cortar Papel</div></button>");
        },

        get_cut_paper: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_cut_paper(context);


        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_paper_cut", "instance.ipf_manager.IpfPrinterCutPaper");

    local.IpfPrinterZClose = instance.web.form.FormWidget.extend({
        events: {
            "click #get_z_close": "get_z_close"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_z_close' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-archive'></div><div>Cierre Z</div></button>");
        },

        get_z_close: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_z_close(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_z_close", "instance.ipf_manager.IpfPrinterZClose");

    local.IpfPrinterZClosePrint = instance.web.form.FormWidget.extend({
        events: {
            "click #get_z_close_print": "get_z_close_print"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_z_close_print' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-print'></div><div>Cierre Z</div></button>");
        },

        get_z_close_print: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_z_close_print(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_z_close_print", "instance.ipf_manager.IpfPrinterZClosePrint");

    local.IpfPrinterNewShift = instance.web.form.FormWidget.extend({
        events: {
            "click #get_new_shift": "get_new_shift"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_new_shift' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-users'></div><div>Cambio de turno</div></button>");
        },

        get_new_shift: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_new_shift(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_new_shift", "instance.ipf_manager.IpfPrinterNewShift");

    local.IpfPrinterNewShiftPrint = instance.web.form.FormWidget.extend({
        events: {
            "click #get_new_shift_print": "get_new_shift_print"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_new_shift_print' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-print'></div><div>Cambio de turno</div></button>");
        },

        get_new_shift_print: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_new_shift_print(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_new_shift_print", "instance.ipf_manager.IpfPrinterNewShiftPrint");

    local.IpfPrinterX = instance.web.form.FormWidget.extend({
        events: {
            "click #get_x": "get_x"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_x' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-file-excel-o'></div><div>Informe X</div></button>");
        },

        get_x: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_x(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_x", "instance.ipf_manager.IpfPrinterX");

    local.IpfPrinterInformationDay = instance.web.form.FormWidget.extend({
        events: {
            "click #get_information_day": "get_information_day"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_information_day' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-calendar'></div><div>Informe de hoy</div></button>");
        },

        get_information_day: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_information_day(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_information_day", "instance.ipf_manager.IpfPrinterInformationDay");

    local.IpfPrinterInformationShift = instance.web.form.FormWidget.extend({
        events: {
            "click #get_information_shift": "get_information_shift"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_information_shift' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-user'></div><div>Informe del turno</div></button>");
        },

        get_information_shift: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_information_shift(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_information_shift", "instance.ipf_manager.IpfPrinterInformationShift");

    local.IpfPrinterGetDocumentHeader = instance.web.form.FormWidget.extend({
        events: {
            "click #get_document_header": "get_document_header"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_document_header' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-bars'></div><div>Infomación de cabezera</div></button>");
        },

        get_document_header: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.get_document_header(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_get_document_header", "instance.ipf_manager.IpfPrinterGetDocumentHeader");

    local.IpfPrinterPostDocumentHeader = instance.web.form.FormWidget.extend({
        events: {
            "click #post_document_header": "post_document_header"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='post_document_header' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-pencil-square-o'></div><div>Editar cabezera</div></button>");
        },

        post_document_header: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            bootbox.prompt({
                title: "Modificar cabezera.",
                value: "",
                callback: function (result) {
                    if (result === null) {
                        return
                    } else {
                        var context = new instance.web.CompoundContext({
                            active_model: self.field_manager.model,
                            active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
                        });
                        var command = new local.ipfAPI();
                        command.post_document_header(context, {"text": result});
                    }
                }
            });
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_post_document_header", "instance.ipf_manager.IpfPrinterPostDocumentHeader");


    local.IpfPrinterDailyBook = instance.web.form.FormWidget.extend({
        events: {
            "click #get_daily_book": "get_daily_book"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='get_daily_book' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-book'></div><div>Libro diario</div></button>");
            bootbox.setDefaults({
                locale: "es"
            });
        },

        get_daily_book: function () {
           var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            bootbox.prompt({
                title: "Extracción de libro diario.",
                value: new Date().toDateInputValue(),
                inputType: "date",
                size: "small",
                callback: function (bookday) {
                    if (!bookday) {
                        return
                    } else {
                        var context = new instance.web.CompoundContext({
                            active_model: self.field_manager.model,
                            active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
                        });
                        var command = new local.ipfAPI();
                        command.get_daily_book(context, bookday);
                    }
                }
            });
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_dailybook", "instance.ipf_manager.IpfPrinterDailyBook");

    local.IpfPrinterPostInvoice = instance.web.form.FormWidget.extend({
        events: {
            "click #post_invoice": "post_invoice"
        },
        start: function () {
            var self = this;
            this.$el.append("<button id='post_invoice' class='oe_inline oe_stat_button'><div class='stat_button_icon fa fa-print'></div><div>Impresora fiscal</div></button>");
        },
        post_invoice: function () {
            var self = this;
            if (!checkBrowserCompatibility()){
                return
            }
            var context = new instance.web.CompoundContext({
                active_model: self.field_manager.model,
                active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            });
            var command = new local.ipfAPI();
            command.post_invoice(context);
        }
    });

    openerp.web.form.custom_widgets.add("ipf_button_post_invoice", "instance.ipf_manager.IpfPrinterPostInvoice");
};