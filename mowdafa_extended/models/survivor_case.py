# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class SurvivorCase(models.Model):
    _name = 'survivor.case'
    _description = 'Survivor Case Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    survivor_id = fields.Many2one(
        'survivor.master',
        string='Survivor',
        required=True,
        tracking=True,
    )
    case_worker_id = fields.Many2one(
        'case.worker',
        string='Case Worker',
        required=True,
        tracking=True,
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    survivor_age = fields.Integer(
        string='Age',
        compute='_compute_survivor_age',
    )
    is_minor = fields.Boolean(
        string='Is Minor',
        compute='_compute_survivor_age',
    )
    guardian_name = fields.Char(
        string='Guardian Name',
        tracking=True,
    )
    guardian_signature = fields.Char(
        string='Guardian Signature',
        copy=False,
    )
    case_worker_signature = fields.Char(
        string='Case Worker Signature',
        related='case_worker_id.code',
        store=True,
        readonly=True,
    )
    survivor_signature = fields.Char(
        string='Survivor Signature',
        related='survivor_id.generated_code',
        store=True,
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes')
    admission_count = fields.Integer(
        string='Admissions',
        compute='_compute_admission_count',
    )

    @api.depends('survivor_id.birth_date')
    def _compute_survivor_age(self):
        today = fields.Date.context_today(self)
        for record in self:
            birth_date = record.survivor_id.birth_date
            if birth_date:
                record.survivor_age = relativedelta(today, birth_date).years
                record.is_minor = record.survivor_age < 18
            else:
                record.survivor_age = 0
                record.is_minor = False

    @api.depends('survivor_id')
    def _compute_admission_count(self):
        for record in self:
            record.admission_count = self.env['admission.form'].search_count(
                [('survivor_id', '=', record.survivor_id.id)]
            ) if record.survivor_id else 0

    def action_view_admissions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Admission Forms',
            'res_model': 'admission.form',
            'view_mode': 'tree,form',
            'domain': [('survivor_id', '=', self.survivor_id.id)],
            'context': {'default_survivor_id': self.survivor_id.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'survivor.case') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
