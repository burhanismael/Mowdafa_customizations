# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CaseClosure(models.Model):
    _name = 'case.closure'
    _description = 'Case Closure Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'case_closure_date desc, id desc'

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
    supervisor_id = fields.Many2one(
        'case.worker',
        string='Supervisor Code',
        tracking=True,
        copy=False,
    )
    closure_summary = fields.Text(
        string='Closure Summary',
        help='Reasons, progress vs action plan, continued-service provisions.',
    )

    # Closure checklist
    checklist_line_ids = fields.One2many(
        'case.closure.checklist.line',
        'closure_id',
        string='Closure Checklist',
        copy=False,
        default=lambda self: self._default_checklist_lines(),
    )
    explanation_notes = fields.Text(string='Explanation Notes')

    @api.model
    def _default_checklist_lines(self):
        return [
            (0, 0, {'question': 'Safety plan has been reviewed and is in place.'}),
            (0, 0, {'question': 'Person has been informed she or he can resume services at anytime.'}),
            (0, 0, {'question': 'Case supervisor has reviewed case closure/exit plan.'}),
        ]

    case_opening_date = fields.Date(string='Case Opening Date', tracking=True)
    case_closure_date = fields.Date(string='Case Closure Date', tracking=True)

    # Signatures
    case_worker_signature = fields.Char(
        string='Caseworker Signature',
        related='case_worker_id.code',
        store=True,
        readonly=True,
    )
    case_worker_signature_date = fields.Date(string='Caseworker Signature Date')
    supervisor_signature = fields.Char(
        string='Supervisor Signature',
        related='supervisor_id.code',
        store=True,
        readonly=True,
    )
    supervisor_signature_date = fields.Date(string='Supervisor Signature Date')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes')

    consent_count = fields.Integer(compute='_compute_related_counts')
    admission_count = fields.Integer(compute='_compute_related_counts')
    action_plan_count = fields.Integer(compute='_compute_related_counts')
    followup_count = fields.Integer(compute='_compute_related_counts')
    referral_count = fields.Integer(compute='_compute_related_counts')

    def _related_domain(self):
        self.ensure_one()
        if self.case_id:
            return [('case_id', '=', self.case_id.id)]
        return [('survivor_id', '=', self.survivor_id.id)]

    @api.depends('survivor_id', 'case_id')
    def _compute_related_counts(self):
        for record in self:
            domain = record._related_domain()
            if record.survivor_id or record.case_id:
                record.consent_count = self.env['survivor.case'].search_count(domain)
                record.admission_count = self.env['admission.form'].search_count(domain)
                record.action_plan_count = self.env['action.plan'].search_count(domain)
                record.followup_count = self.env['followup.form'].search_count(domain)
                record.referral_count = self.env['referral.form'].search_count(domain)
            else:
                record.consent_count = 0
                record.admission_count = 0
                record.action_plan_count = 0
                record.followup_count = 0
                record.referral_count = 0

    def _action_view_related(self, res_model, name):
        self.ensure_one()
        domain = self._related_domain()
        context = {'default_survivor_id': self.survivor_id.id}
        if self.case_id:
            context['default_case_id'] = self.case_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': res_model,
            'view_mode': 'tree,form',
            'domain': domain,
            'context': context,
        }

    def action_view_consent_forms(self):
        return self._action_view_related('survivor.case', 'Consent Forms')

    def action_view_admissions(self):
        return self._action_view_related('admission.form', 'Admission Forms')

    def action_view_action_plans(self):
        return self._action_view_related('action.plan', 'Action Plans')

    def action_view_followups(self):
        return self._action_view_related('followup.form', 'Follow-up Forms')

    def action_view_referrals(self):
        return self._action_view_related('referral.form', 'Referral Forms')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'case.closure') or 'New'
        records = super().create(vals_list)
        records.case_id._advance_service_stage('closure')
        return records

    def action_close(self):
        for record in self:
            if not record.checklist_line_ids or any(
                    line.answer != 'yes' for line in record.checklist_line_ids):
                raise UserError(_(
                    'The case cannot be closed until every point of the '
                    'closure checklist is answered YES: safety plan reviewed, '
                    'client informed they may resume services, and supervisor '
                    'reviewed the exit plan.'
                ))
            if not record.case_opening_date or not record.case_closure_date:
                raise UserError(_(
                    'Please record both the case opening date and the case '
                    'closure date before closing.'
                ))
            if not record.supervisor_id:
                raise UserError(_(
                    'Supervisor sign-off is required before the case can be '
                    'closed.'
                ))
        self.write({'state': 'closed'})

    def action_reopen(self):
        for record in self:
            record.message_post(
                body=_('Case re-opened: client may resume services at any time.'))
        self.write({'state': 'draft'})


class CaseClosureChecklistLine(models.Model):
    _name = 'case.closure.checklist.line'
    _description = 'Case Closure Checklist Line'

    closure_id = fields.Many2one(
        'case.closure',
        string='Case Closure',
        required=True,
        ondelete='cascade',
    )
    question = fields.Char(string='Checklist Point', required=True)
    answer = fields.Selection([
        ('yes', 'YES'),
        ('no', 'NO'),
    ], string='YES/NO')
    explain = fields.Char(string='NO (explain)')
