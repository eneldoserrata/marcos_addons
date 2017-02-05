odoo.define('ipf_manager.models', function (require) {
    //'use strict';

    var devices = require('point_of_sale.devices');
    var models = require('point_of_sale.models');


    models.load_models({
        model: 'ipf.printer.config',
        fields: ["host", 'print_source', 'print_copy', 'subsidiary'],
        domain: function (self) {
            return [['id', '=', self.config.iface_fiscal_printer[0]]];
        },
        loaded: function (self, configs) {
            if (configs.length > 0) {
                self.config.iface_fiscal_printer_host = configs[0].host || false;
                self.config.iface_fiscal_printer_source = configs[0].print_source || false;
                self.config.iface_fiscal_printer_copy = configs[0].print_copy || false;
                self.config.iface_fiscal_printer_subsidiary = configs[0].subsidiary || false;
            }
        },


    });

    models.load_models({
        model:  'account.journal',
        fields: ['type', 'sequence', 'ipf_payment_type'],
        domain: function(self,tmp){ return [['id','in',tmp.journals]]; },
        loaded: function(self, journals){
            var i;
            self.journals = journals;

            // associate the bank statements with their journals.
            var cashregisters = self.cashregisters;
            var ilen = cashregisters.length;
            for(i = 0; i < ilen; i++){
                for(var j = 0, jlen = journals.length; j < jlen; j++){
                    if(cashregisters[i].journal_id[0] === journals[j].id){
                        cashregisters[i].journal = journals[j];
                    }
                }
            }

            self.cashregisters_by_id = {};
            for (i = 0; i < self.cashregisters.length; i++) {
                self.cashregisters_by_id[self.cashregisters[i].id] = self.cashregisters[i];
            }

            self.cashregisters = self.cashregisters.sort(function(a,b){
		// prefer cashregisters to be first in the list
		if (a.journal.type == "cash" && b.journal.type != "cash") {
		    return -1;
		} else if (a.journal.type != "cash" && b.journal.type == "cash") {
		    return 1;
		} else {
                    return a.journal.sequence - b.journal.sequence;
		}
            });

        },
    });

});



