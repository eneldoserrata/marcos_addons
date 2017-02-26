# -*- coding: utf-8 -*-
import itertools

from odoo import models, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.constrains("name")
    def onchange_name(self):
        existing_names = self.env[self._name].search([('name', '=', self.name)])
        if existing_names:
            self.env.invalidate_all()
            name_list = [(rec.id, rec.name) for rec in existing_names]
            wizard = self.env["prevent.duplicate.name.wizard"].create({"name_list": str(name_list)})
            view_id = self.env.ref("prevent_name_duplicate.prevent_duplicate_name_wizard_form")
            return {
                'name': 'Nombre duplicado',
                'type': 'ir.actions.act_window',
                'res_model': 'prevent.duplicate.name.wizard',
                'res_id': wizard.id,
                'view_id': view_id.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new'}
