# -*- coding: utf-8 -*-


from openerp import models, fields, api

import time


class PosConfig(models.Model):
    _inherit = "pos.config"


    iface_fiscal_printer = fields.Many2one("ipf.printer.config", string="Impresora fiscal")


class PosOrder(models.Model):
    _inherit = "pos.order"


    @api.model
    def get_fiscal_data(self, name):
        reserve_ncf_seq = False
        reference_ncf = False
        res = {}
        while not reserve_ncf_seq:
            time.sleep(1)
            order = self.search([('pos_reference', '=', name)])
            reserve_ncf_seq = order.reserve_ncf_seq

        if not order.origin:
            client_fiscal_type = order.invoice_id.fiscal_position_id.client_fiscal_type
            import pdb;pdb.set_trace()
            if client_fiscal_type == "gov":
                client_fiscal_type = "fiscal"
        else:
            reference_ncf = order.origin.invoice_id.number
            if reference_ncf[9:11] in ('01','14'):
                client_fiscal_type = "fiscal_note"
            if reference_ncf[9:11] == "15":
                client_fiscal_type = "special_note"
            else:
                client_fiscal_type = "final_note"


        res.update({"ncf": reserve_ncf_seq, "type": client_fiscal_type, "reference_ncf": reference_ncf})



        return res




