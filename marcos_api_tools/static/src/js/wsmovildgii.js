odoo.define('ncf_manager.wsmovildgii', function (require) {
    "use strict";

    var form_common = require('web.form_common');

    var wsMovilDGII = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
        start: function () {
            // this.$el.append("<button id='open' class='btn btn-default btn-block'><div class='stat_button_icon fa fa-info fa-fw'></div><div>Buscar en DGII</div></button>");
        },
        get_software_version: function () {
            // var self = this;
            // if (!checkBrowserCompatibility()) {
            //     return
            // }
            // var context = new web_data.CompoundContext({
            //     active_model: self.field_manager.model,
            //     active_id: self.field_manager.datarecord.id || self.field_manager.dataset.context.id
            // });
            // var command = new ipfAPI();
            // command.get_software_version(context);
        }
    });

    core.form_custom_registry.add("ipf_button_softwareVersion", IpfsoftwareVersion);

});