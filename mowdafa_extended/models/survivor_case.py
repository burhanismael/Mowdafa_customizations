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
        tracking=True,
        copy=False,
    )
    case_worker_id = fields.Many2one(
        'case.worker',
        string='Case Worker',
        tracking=True,
        copy=False,
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
    ], string='Status', default='draft', tracking=True, copy=False)
    notes = fields.Text(string='Notes')
    admission_count = fields.Integer(
        string='Admissions',
        compute='_compute_related_counts',
    )
    action_plan_count = fields.Integer(compute='_compute_related_counts')
    followup_count = fields.Integer(compute='_compute_related_counts')
    referral_count = fields.Integer(compute='_compute_related_counts')
    closure_count = fields.Integer(compute='_compute_related_counts')

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
    def _compute_related_counts(self):
        for record in self:
            domain = [('survivor_id', '=', record.survivor_id.id)]
            if record.survivor_id:
                record.admission_count = self.env['admission.form'].search_count(domain)
                record.action_plan_count = self.env['action.plan'].search_count(domain)
                record.followup_count = self.env['followup.form'].search_count(domain)
                record.referral_count = self.env['referral.form'].search_count(domain)
                record.closure_count = self.env['case.closure'].search_count(domain)
            else:
                record.admission_count = 0
                record.action_plan_count = 0
                record.followup_count = 0
                record.referral_count = 0
                record.closure_count = 0

    def _action_view_related(self, res_model, name):
        self.ensure_one()
        records = self.env[res_model].search(
            [('survivor_id', '=', self.survivor_id.id)])
        action = {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': res_model,
            'view_mode': 'tree,form',
            'domain': [('survivor_id', '=', self.survivor_id.id)],
            'context': {'default_survivor_id': self.survivor_id.id},
        }
        if len(records) == 1:
            action.update({'view_mode': 'form', 'res_id': records.id})
        return action

    def action_open_admission(self):
        self.ensure_one()
        admission = self.env['admission.form'].search(
            [('survivor_id', '=', self.survivor_id.id)], limit=1)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Admission Form',
            'res_model': 'admission.form',
            'view_mode': 'form',
            'context': {
                'default_survivor_id': self.survivor_id.id,
                'default_consent_form_id': self.id,
            },
        }
        if admission:
            action['res_id'] = admission.id
        return action

    def action_view_admissions(self):
        return self._action_view_related('admission.form', 'Admission Forms')

    def action_view_action_plans(self):
        return self._action_view_related('action.plan', 'Action Plans')

    def action_view_followups(self):
        return self._action_view_related('followup.form', 'Follow-up Forms')

    def action_view_referrals(self):
        return self._action_view_related('referral.form', 'Referral Forms')

    def action_view_closures(self):
        return self._action_view_related('case.closure', 'Case Closures')

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
