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
