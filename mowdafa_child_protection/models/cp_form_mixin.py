# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CpFormMixin(models.AbstractModel):
    """Every CP form carries its own sequence reference and a chatter."""
    _name = 'cp.form.mixin'
    _description = 'CP Form Mixin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sequence_code = None

    name = fields.Char(
        string='Reference', readonly=True, copy=False, default='New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New' and self._sequence_code:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    self._sequence_code) or 'New'
        return super().create(vals_list)

    def action_view_case(self):
        """Open the parent case from any satellite form."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Case'),
            'res_model': 'cp.case',
            'view_mode': 'form',
            'res_id': self.case_id.id,
        }
