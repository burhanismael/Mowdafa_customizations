# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FollowupForm(models.Model):
    _name = 'followup.form'
    _description = 'Follow-up Form'
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

    # Progress towards goals
    goal_line_ids = fields.One2many(
        'followup.goal.line',
        'followup_id',
        string='Progress Towards Goals',
        copy=False,
        default=lambda self: self._default_goal_lines(),
    )

    @api.model
    def _default_goal_lines(self):
        return [
            (0, 0, {'domain_type': 'Safety'}),
            (0, 0, {'domain_type': 'Health Care'}),
            (0, 0, {'domain_type': 'Psychosocial Support'}),
            (0, 0, {'domain_type': 'Access to Justice'}),
            (0, 0, {'domain_type': 'Other (list other goals made here)'}),
        ]

    other_observations = fields.Text(
        string='Other Observations/Caseworker Notes',
    )

    # Re-assessing safety
    safety_line_ids = fields.One2many(
        'followup.safety.line',
        'followup_id',
        string='Re-assessing Safety',
        copy=False,
        default=lambda self: self._default_safety_lines(),
    )

    @api.model
    def _default_safety_lines(self):
        return [
            (0, 0, {'question': 'Are there new or continued risks of danger at home?'}),
            (0, 0, {'question': 'Are there any new or ongoing safety issues the survivor is facing in the community?'}),
        ]

    # Final assessment
    assessment_line_ids = fields.One2many(
        'followup.assessment.line',
        'followup_id',
        string='Final Assessment',
        copy=False,
        default=lambda self: self._default_assessment_lines(),
    )

    @api.model
    def _default_assessment_lines(self):
        return [
            (0, 0, {'question': 'Safety situation is stable (survivor is physically safe, and/or has a plan to keep physically safe)'}),
            (0, 0, {'question': 'Health situation is stable (survivor has no medical problems that require treatment)'}),
            (0, 0, {'question': 'Psychosocial wellbeing has improved (survivor is engaging in regular behavior, has a safe person to talk to)'}),
            (0, 0, {'question': 'Access to Justice secured (if applicable)'}),
            (0, 0, {'question': 'Other Intervention Needed'}),
        ]

    # Next follow-up meeting
    next_followup_datetime = fields.Datetime(
        string='Next Follow-up (Date/Time)',
        tracking=True,
    )
    next_followup_location = fields.Char(
        string='Next Follow-up Location',
        tracking=True,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes')

    consent_count = fields.Integer(compute='_compute_related_counts')
    admission_count = fields.Integer(compute='_compute_related_counts')
    action_plan_count = fields.Integer(compute='_compute_related_counts')
    closure_count = fields.Integer(compute='_compute_related_counts')

    @api.depends('survivor_id')
    def _compute_related_counts(self):
        for record in self:
            domain = [('survivor_id', '=', record.survivor_id.id)]
            if record.survivor_id:
                record.consent_count = self.env['survivor.case'].search_count(domain)
                record.admission_count = self.env['admission.form'].search_count(domain)
                record.action_plan_count = self.env['action.plan'].search_count(domain)
                record.closure_count = self.env['case.closure'].search_count(domain)
            else:
                record.consent_count = 0
                record.admission_count = 0
                record.action_plan_count = 0
                record.closure_count = 0

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

    def action_view_action_plans(self):
        return self._action_view_related('action.plan', 'Action Plans')

    def action_view_closures(self):
        return self._action_view_related('case.closure', 'Case Closures')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'followup.form') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class FollowupGoalLine(models.Model):
    _name = 'followup.goal.line'
    _description = 'Follow-up Goal Progress Line'

    followup_id = fields.Many2one(
        'followup.form',
        string='Follow-up Form',
        required=True,
        ondelete='cascade',
    )
    domain_type = fields.Char(string='Goal Domain', required=True)
    status = fields.Selection([
        ('met', 'Met'),
        ('not_met', 'Not Met'),
    ], string='Status')
    explanation = fields.Html(string='Explain')


class FollowupAssessmentLine(models.Model):
    _name = 'followup.assessment.line'
    _description = 'Follow-up Final Assessment Line'

    followup_id = fields.Many2one(
        'followup.form',
        string='Follow-up Form',
        required=True,
        ondelete='cascade',
    )
    question = fields.Char(string='Assessment', required=True)
    answer = fields.Selection([
        ('yes', 'Y'),
        ('no', 'N'),
    ], string='Y/N')
    explain = fields.Html(string='Explain')
    intervention = fields.Html(string='Additional Interventions Planned')


class FollowupSafetyLine(models.Model):
    _name = 'followup.safety.line'
    _description = 'Follow-up Safety Re-assessment Line'

    followup_id = fields.Many2one(
        'followup.form',
        string='Follow-up Form',
        required=True,
        ondelete='cascade',
    )
    question = fields.Char(string='Question', required=True)
    answer = fields.Selection([
        ('yes', 'Y'),
        ('no', 'N'),
    ], string='Y/N')
    explain = fields.Html(string='Explain')
    intervention = fields.Html(string='Additional Intervention Planned')
