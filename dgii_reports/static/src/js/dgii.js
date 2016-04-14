/**
 * Created by eneldoserrata on 4/2/16.
 */
odoo.define('dgii.reports', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var ControlPanelMixin = require('web.ControlPanelMixin');

    var core = require('web.core');
    var Model = require('web.DataModel');

    var DgiiWelcome = Widget.extend({
        template: "dgii-report-welcome"
    });

    var abstractDgiiReports = Widget.extend({
        template: "dgii_reports_template",
        init: function () {
            this._super();
            this.current_view = new DgiiWelcome(this);
        },
        start: function () {
            var self = this;
            this.current_view.appendTo(this.$el);

            this.$el.find("#dgii-report-select").change(function () {
                var selected = $(this).find(":selected").text();
                if (selected == "IT-1") {
                    self.current_view.destroy();
                    self.current_view = new DgiiReportIT(self);
                    self.current_view.appendTo(self.$el);
                    self.$el.find("#dgii_report_refresh").on("click", function(){
                        self.render_it();
                    })

                } else {
                    self.current_view.destroy();
                    self.current_view = new DgiiWelcome(self);
                    self.current_view.appendTo(self.$el);
                }
            })
        },
        render_it: function(){
            var self = this;
            var month = self.$el.find("#itmonth");
            var year = self.$el.find("#ityear");

            new Model("dgii.report.it1").call("get_report", [month.val(), year.val()])
                .then(function(result){
                    if (result==false){
                        alert("Verifique el mes y año e intente de nuevo!")
                    }else{
                        $.each(result, function(key, value){
                            var amount = 0;
                            if (value.base_amount) {
                                amount = value.base
                            } else {
                                amount = value.tax
                            }
                           $("."+key).text(amount)
                        });
                    }

                })
        }
    });

    var DgiiReportIT = Widget.extend({
        template: "dgii_reports_template_it1",
    });

    core.action_registry.add('abstractDgiiReports_view', abstractDgiiReports);

});
