# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SurvivorMaster(models.Model):
    _name = 'survivor.master'
    _description = 'Survivor Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'generated_code'
    _rec_names_search = ['generated_code', 'survivor_name']
    _order = 'id desc'

    survivor_name = fields.Char(
        string='Survivor Name',
        required=True,
        tracking=True,
    )
    mother_first_name = fields.Char(
        string="Mother's First Name",
        required=True,
        tracking=True,
    )
    birth_date = fields.Date(
        string='Birth Date',
        required=True,
        tracking=True,
    )
    birth_order = fields.Char(
        string='Birth Order (Digits)',
        required=True,
        tracking=True,
    )
    place_of_birth = fields.Char(
        string='Place of Birth',
        required=True,
        tracking=True,
    )
    generated_code = fields.Char(
        string='Generated Code',
        compute='_compute_generated_code',
        store=True,
        tracking=True,
    )

    consent_count = fields.Integer(
        string='Consent Forms',
        compute='_compute_consent_count',
    )

    def _compute_consent_count(self):
        for record in self:
            record.consent_count = self.env['survivor.case'].search_count(
                [('survivor_id', '=', record.id)]
            )

    def action_view_consent_forms(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consent Forms',
            'res_model': 'survivor.case',
            'view_mode': 'tree,form',
            'domain': [('survivor_id', '=', self.id)],
            'context': {'default_survivor_id': self.id},
        }

    @api.model
    def _pad_birth_order(self, vals):
        birth_order = (vals.get('birth_order') or '').strip()
        if birth_order.isdigit() and len(birth_order) < 3:
            vals['birth_order'] = birth_order.zfill(3)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._pad_birth_order(vals)
        return super().create(vals_list)

    def write(self, vals):
        if 'birth_order' in vals:
            self._pad_birth_order(vals)
        return super().write(vals)

    @api.onchange('birth_order')
    def _onchange_birth_order(self):
        for record in self:
            birth_order = (record.birth_order or '').strip()
            if birth_order.isdigit() and len(birth_order) < 3:
                record.birth_order = birth_order.zfill(3)

    def init(self):
        self.env.cr.execute(
            "UPDATE survivor_master SET generated_code = UPPER(generated_code) "
            "WHERE generated_code IS NOT NULL AND generated_code != UPPER(generated_code)"
        )

    @api.depends('mother_first_name', 'birth_date',
                 'birth_order', 'place_of_birth')
    def _compute_generated_code(self):
        for record in self:
            birth_year = ''
            birth_month = ''
            if record.birth_date:
                birth_year = record.birth_date.strftime('%Y')
                birth_month = record.birth_date.strftime('%B')
            parts = [
                record.mother_first_name,
                birth_year,
                birth_month,
                record.birth_order,
                record.place_of_birth,
            ]
            code = ''
            for value in parts:
                value = (value or '').strip().upper()
                code += value[2] if len(value) >= 3 else ''
            record.generated_code = code
