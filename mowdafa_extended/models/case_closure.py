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
    )
    case_worker_id = fields.Many2one(
        'case.worker',
        string='Caseworker Code',
        required=True,
        tracking=True,
    )
    supervisor_id = fields.Many2one(
        'case.worker',
        string='Supervisor Code',
        tracking=True,
    )
    closure_summary = fields.Text(
        string='Closure Summary',
        help='Reasons, progress vs action plan, continued-service provisions.',
    )

    # Closure checklist
    safety_plan_reviewed = fields.Boolean(
        string='Safety Plan Reviewed?',
        tracking=True,
    )
    safety_plan_note = fields.Text(string='Safety Plan Note')
    client_informed_resume = fields.Boolean(
        string='Client Informed She/He May Resume Services?',
        tracking=True,
    )
    client_informed_note = fields.Text(string='Client Informed Note')
    supervisor_reviewed = fields.Boolean(
        string='Supervisor Reviewed Exit Plan?',
        tracking=True,
    )
    supervisor_reviewed_note = fields.Text(string='Supervisor Review Note')

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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'case.closure') or 'New'
        return super().create(vals_list)

    def action_close(self):
        for record in self:
            if not (record.safety_plan_reviewed
                    and record.client_informed_resume
                    and record.supervisor_reviewed):
                raise UserError(_(
                    'The case cannot be closed until the three-point checklist '
                    'is satisfied: safety plan reviewed, client informed they '
                    'may resume services, and supervisor reviewed the exit plan.'
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
