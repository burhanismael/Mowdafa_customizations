# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


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
    photo = fields.Binary(string='Photo', attachment=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
    ], string='Status', default='draft', required=True, tracking=True,
        copy=False)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_reset_draft(self):
        if not self.env.user.has_group(
                'mowdafa_extended.group_reset_to_draft'):
            raise AccessError(_(
                'Only users in the "Reset to Draft" group may unlock an '
                'active record.'))
        self.write({'state': 'draft'})

    @api.constrains('survivor_name', 'mother_first_name', 'birth_date')
    def _check_unique_survivor(self):
        """A survivor is identified by name + mother's first name + birth
        date. The same three together means it's the same person already
        on file."""
        for record in self:
            if not (record.survivor_name and record.mother_first_name
                    and record.birth_date):
                continue
            duplicate = self.search([
                ('id', '!=', record.id),
                ('survivor_name', '=ilike', record.survivor_name.strip()),
                ('mother_first_name', '=ilike',
                 record.mother_first_name.strip()),
                ('birth_date', '=', record.birth_date),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    'A survivor with the same Name, Mother\'s First Name '
                    'and Birth Date already exists (%s). This looks like '
                    'the same person — open that record instead of '
                    'creating a duplicate.', duplicate.generated_code
                    or duplicate.survivor_name))
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
