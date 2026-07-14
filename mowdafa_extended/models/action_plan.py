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
    goal_ids = fields.One2many(
        'action.plan.goal',
        'plan_id',
        string='Action Points / Goals',
    )
    can_provide_services = fields.Boolean(
        string='Can MOWDAFA provide all required services?',
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'action.plan') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

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
