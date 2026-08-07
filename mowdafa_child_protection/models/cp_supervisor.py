# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CpSupervisor(models.Model):
    """Child Protection supervisor master — same shape as the GBV
    survivor.master: identified by name + mother's first name + birth
    date, with an auto-generated code."""
    _name = 'cp.supervisor'
    _description = 'CP Supervisor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'generated_code'
    _rec_names_search = ['generated_code', 'supervisor_name']
    _order = 'id desc'

    supervisor_name = fields.Char(
        string='Supervisor Name', required=True, tracking=True)
    photo = fields.Binary(string='Photo', attachment=True)
    mother_first_name = fields.Char(
        string="Mother's First Name", required=True, tracking=True)
    birth_date = fields.Date(string='Birth Date', required=True, tracking=True)
    birth_order = fields.Char(
        string='Birth Order (Digits)', required=True, tracking=True)
    place_of_birth = fields.Char(
        string='Place of Birth', required=True, tracking=True)
    generated_code = fields.Char(
        string='Generated Code', compute='_compute_generated_code',
        store=True, tracking=True)
    case_ids = fields.One2many(
        'cp.case', 'supervisor_id', string='Linked Cases')
    case_count = fields.Integer(
        string='Cases', compute='_compute_case_count')

    @api.depends('case_ids')
    def _compute_case_count(self):
        for record in self:
            record.case_count = len(record.case_ids)

    def action_view_cases(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cases'),
            'res_model': 'cp.case',
            'view_mode': 'tree,form',
            'domain': [('supervisor_id', '=', self.id)],
            'context': {'default_supervisor_id': self.id},
        }

    @api.constrains('supervisor_name', 'mother_first_name', 'birth_date')
    def _check_unique_supervisor(self):
        for record in self:
            if not (record.supervisor_name and record.mother_first_name
                    and record.birth_date):
                continue
            duplicate = self.search([
                ('id', '!=', record.id),
                ('supervisor_name', '=ilike', record.supervisor_name.strip()),
                ('mother_first_name', '=ilike',
                 record.mother_first_name.strip()),
                ('birth_date', '=', record.birth_date),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    'A record with the same Name, Mother\'s First Name and '
                    'Birth Date already exists (%s).', duplicate.generated_code
                    or duplicate.supervisor_name))

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
