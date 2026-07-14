# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ActionPlan(models.Model):
    _name = 'action.plan'
    _description = 'Action Plan'
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
        string='Survivor Code',
        required=True,
        tracking=True,
        copy=False,
    )
    case_worker_id = fields.Many2one(
        'case.worker',
        string='Caseworker Code',
        required=True,
        tracking=True,
        copy=False,
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    goal_ids = fields.One2many(
        'action.plan.goal',
        'plan_id',
        string='Action Points / Goals',
        copy=False,
    )
    can_provide_services = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Can MOWDAFA provide all required services?',
        required=True,
        tracking=True,
    )
    followup_datetime = fields.Datetime(
        string='Follow-up Meeting (Date/Time)',
        tracking=True,
    )
    followup_location = fields.Char(
        string='Follow-up Location',
        tracking=True,
    )
    case_worker_signature = fields.Char(
        string='Caseworker Signature',
        related='case_worker_id.code',
        store=True,
        readonly=True,
    )
    case_worker_signature_date = fields.Date(string='Caseworker Signature Date')
    survivor_signature = fields.Char(
        string='Client Signature',
        related='survivor_id.generated_code',
        store=True,
        readonly=True,
    )
    client_signature_date = fields.Date(string='Client Signature Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes')

    consent_count = fields.Integer(compute='_compute_related_counts')
    admission_count = fields.Integer(compute='_compute_related_counts')
    followup_count = fields.Integer(compute='_compute_related_counts')
    referral_count = fields.Integer(compute='_compute_related_counts')

    @api.depends('survivor_id')
    def _compute_related_counts(self):
        for record in self:
            domain = [('survivor_id', '=', record.survivor_id.id)]
            if record.survivor_id:
                record.consent_count = self.env['survivor.case'].search_count(domain)
                record.admission_count = self.env['admission.form'].search_count(domain)
                record.followup_count = self.env['followup.form'].search_count(domain)
                record.referral_count = self.env['referral.form'].search_count(domain)
            else:
                record.consent_count = 0
                record.admission_count = 0
                record.followup_count = 0
                record.referral_count = 0

    def _action_view_related(self, res_model, name):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': res_model,
            'view_mode': 'tree,form',
            'domain': [('survivor_id', '=', self.survivor_id.id)],
            'context': {'default_survivor_id': self.survivor_id.id},
        }

    def action_view_consent_forms(self):
        return self._action_view_related('survivor.case', 'Consent Forms')

    def action_view_admissions(self):
        return self._action_view_related('admission.form', 'Admission Forms')

    def action_view_followups(self):
        return self._action_view_related('followup.form', 'Follow-up Forms')

    def action_view_referrals(self):
        return self._action_view_related('referral.form', 'Referral Forms')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'action.plan') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_create_followup(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Follow-up Form',
            'res_model': 'followup.form',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_survivor_id': self.survivor_id.id,
                'default_case_worker_id': self.case_worker_id.id,
            },
        }

    def action_create_referral(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Referral Form',
            'res_model': 'referral.form',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_survivor_id': self.survivor_id.id,
            },
        }

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class ActionPlanGoal(models.Model):
    _name = 'action.plan.goal'
    _description = 'Action Plan Goal'

    plan_id = fields.Many2one(
        'action.plan',
        string='Action Plan',
        required=True,
        ondelete='cascade',
    )
    goal = fields.Char(string='Goal', required=True)
    who = fields.Char(string='Who')
    by_when = fields.Date(string='By When')
