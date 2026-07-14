# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ReferralService(models.Model):
    _name = 'referral.service'
    _description = 'Referral Service Type'
    _order = 'sequence, id'

    name = fields.Char(string='Service', required=True)
    sequence = fields.Integer(string='Sequence', default=10)


class ReferralForm(models.Model):
    _name = 'referral.form'
    _description = 'Inter-Agency Referral Form (Form 9)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'referral_date desc, id desc'

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
    priority = fields.Selection([
        ('high', 'High Risk (48 hours)'),
        ('medium', 'Medium Risk (1-7 days)'),
        ('low', 'Low Risk'),
    ], string='Priority', required=True, default='medium', tracking=True)
    date_identification = fields.Date(
        string='Date of Identification',
        tracking=True,
    )
    referral_date = fields.Date(
        string='Referral Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )

    # Referred by (referring agency)
    ref_sector = fields.Char(string='Sector')
    ref_agency = fields.Char(string='Agency')
    ref_location = fields.Char(string='Location')
    ref_focal_point = fields.Char(string='Focal Point Name')
    ref_email = fields.Char(string='Email')
    ref_phone = fields.Char(string='Phone')

    # Referred to (receiving agency)
    recv_sector = fields.Char(string='Sector')
    recv_agency = fields.Char(string='Agency')
    recv_location = fields.Char(string='Location')
    recv_focal_point = fields.Char(string='Focal Point Name')
    recv_email = fields.Char(string='Email')
    recv_phone = fields.Char(string='Phone')

    # Consent / client information (data minimisation: only with consent)
    consent_obtained = fields.Boolean(
        string='Consent Obtained?',
        tracking=True,
    )
    client_name = fields.Char(string='Client Name')
    client_address = fields.Char(string='Address')
    client_phone = fields.Char(string='Phone')
    client_phone_owner = fields.Char(string='Phone Owner')
    contact_method = fields.Selection([
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('in_person', 'In Person'),
        ('other', 'Other'),
    ], string='Preferred Contact Method')
    preferred_contact_datetime = fields.Datetime(string='Preferred Date/Time')

    # Client bio
    unhcr_no = fields.Char(string='UNHCR Registration No.')
    population_type = fields.Selection([
        ('host', 'Host Community'),
        ('idp', 'IDP'),
    ], string='Population Type')
    client_age = fields.Integer(string='Age')
    client_sex = fields.Selection([
        ('female', 'Female'),
        ('male', 'Male'),
    ], string='Sex')
    disability_status = fields.Boolean(
        string='Disability Status (Washington Group)?',
    )

    # Caregiver information
    caregiver_name = fields.Char(string='Caregiver Name')
    caregiver_affiliation = fields.Char(string='Affiliation')
    caregiver_relationship = fields.Char(string='Relationship to Client')
    caregiver_address = fields.Char(string='Caregiver Address')
    caregiver_phone = fields.Char(string='Caregiver Phone')
    caregiver_informed = fields.Boolean(string='Caregiver Informed of Referral?')
    caregiver_informed_explanation = fields.Text(string='Explanation')

    # Services and narrative
    service_ids = fields.Many2many(
        'referral.service',
        string='Referral for Which Service',
    )
    case_narrative = fields.Text(
        string='Case Narrative',
        help='Minimum information the receiving agency needs, plus any '
             'accessibility / reasonable-accommodation measures. For GBV, '
             'child-protection and legal case-management referrals, exclude '
             'incident details.',
    )

    # Consent to release information
    consent_client_name = fields.Char(string='Client Name (Consent)')
    consent_provider_name = fields.Char(string='Service Provider Name')
    consent_client_signature = fields.Char(string='Client Signature')
    consent_provider_signature = fields.Char(string='Provider Signature')
    consent_date = fields.Date(string='Consent Date')

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
                    'referral.form') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
