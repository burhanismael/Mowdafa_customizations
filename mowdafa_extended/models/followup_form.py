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
    )
    case_worker_id = fields.Many2one(
        'case.worker',
        string='Caseworker Code',
        required=True,
        tracking=True,
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
    )

    # Re-assessing safety
    risk_at_home = fields.Boolean(
        string='New/Continued Risks at Home?',
        tracking=True,
    )
    risk_at_home_action = fields.Text(string='Action (Risks at Home)')
    risk_in_community = fields.Boolean(
        string='Safety Issues in Community?',
        tracking=True,
    )
    risk_in_community_action = fields.Text(string='Action (Community Safety)')

    # Final assessment
    safety_stable = fields.Boolean(string='Safety Stable?')
    safety_stable_note = fields.Text(string='Safety Note')
    health_stable = fields.Boolean(string='Health Stable?')
    health_stable_note = fields.Text(string='Health Note')
    psychosocial_improved = fields.Boolean(string='Psychosocial Improved?')
    psychosocial_improved_note = fields.Text(string='Psychosocial Note')
    justice_secured = fields.Boolean(string='Access to Justice Secured?')
    justice_secured_note = fields.Text(string='Justice Note')
    other_intervention_needed = fields.Boolean(string='Other Intervention Needed?')
    other_intervention_note = fields.Text(string='Other Intervention Note')

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
    domain_type = fields.Selection([
        ('safety', 'Safety'),
        ('health', 'Health Care'),
        ('psychosocial', 'Psychosocial Support'),
        ('justice', 'Access to Justice'),
        ('other', 'Other'),
    ], string='Goal Domain', required=True)
    status = fields.Selection([
        ('met', 'Met'),
        ('not_met', 'Not Met'),
    ], string='Status')
    explanation = fields.Char(string='Explanation')
