# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CpRegistration(models.Model):
    """CP-07/08 — the child becomes a person here: identity, two
    separate consents, protection concerns, immediate actions and the
    withholding choices."""
    _name = 'cp.registration'
    _description = 'CP Registration (CP-07/08)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.registration'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')

    # ── child summary (read from the case, for the header) ───────────────
    child_full_name = fields.Char(
        related='case_id.child_name', string='Child Full Name')
    child_sex = fields.Selection(related='case_id.sex', string='Sex')
    child_dob = fields.Date(
        related='case_id.date_of_birth', string='Date of Birth')
    child_nationality = fields.Char(
        related='case_id.nationality', string='Nationality')

    # ── 1 · registration details ─────────────────────────────────────────
    date = fields.Date(
        string='Date of Registration', required=True,
        default=fields.Date.context_today)
    population_group = fields.Selection(
        related='case_id.population_group', string='Population Group',
        readonly=False)
    country_id = fields.Many2one('res.country', string='Country')
    region_id = fields.Many2one('gbv.region', string='Region')
    district_id = fields.Many2one(
        'gbv.district', string='District / Town',
        domain="[('region_id', '=?', region_id)]")
    village = fields.Char(string='Village / Section')
    date_of_arrival = fields.Date(string='Date of Arrival')

    # ── consent ──────────────────────────────────────────────────────────
    consent_registration = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Does the Child give informed consent to the registration?')
    consent_registration_by = fields.Char(string='Given By')
    child_assent = fields.Boolean(string="Child's Assent")
    consent_data = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Does the child (or caregiver) give informed consent for '
              'their data to be stored and shared?')
    consent_data_limits = fields.Char(string='Limits')

    # ── child's personal details (rapid registration assessment) ─────────
    nickname = fields.Char(string='Also Known As (Nickname)')
    father_name = fields.Char(string='Father — Full Name')
    father_tel = fields.Char(string='Father — Tel')
    mother_name = fields.Char(string='Mother — Full Name')
    mother_tel = fields.Char(string='Mother — Tel')
    relative_name = fields.Char(string='Relative — Full Name')
    relative_tel = fields.Char(string='Relative — Tel')
    household_tel = fields.Char(string='Telephone (child / household)')
    nationality_origin = fields.Char(string='Nationality / Country of Origin')

    # ── A9 · schooling ───────────────────────────────────────────────────
    prev_schooling = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Previous schooling?')
    highest_grade = fields.Char(string='Highest Grade Completed')
    literacy_level = fields.Selection([
        ('reads', 'Reads'),
        ('writes', 'Writes'),
        ('neither', 'Neither'),
    ], string='Current Literacy Level')
    wants_to_learn = fields.Text(
        string='Interest in learning or vocational training')

    # ── place of birth / origin ──────────────────────────────────────────
    pob_region = fields.Char(string='Region (Place of Birth)')
    pob_district = fields.Char(string='District / Town (Place of Birth)')
    pob_village = fields.Char(string='Village / Camp (Place of Birth)')

    # ── current address ──────────────────────────────────────────────────
    addr_region = fields.Char(string='Region (Current Address)')
    addr_district = fields.Char(string='District / Town (Current Address)')
    addr_village = fields.Char(string='Village / Camp (Current Address)')

    # ── identification & referral details ────────────────────────────────
    found_at = fields.Char(string='Place where child was found / brought from')
    referrer_type = fields.Selection([
        ('police', 'Police'),
        ('ngo', 'NGO'),
        ('community', 'Community Member'),
        ('self', 'Self'),
        ('other', 'Other'),
    ], string='Referring person / organization')
    referrer_name = fields.Char(string='Referring organization — Full Name')
    referrer_contact = fields.Char(string='Referring organization — Contact')
    referral_reason = fields.Text(string='Reason for referral / rescue')

    # ── current care arrangements of the child ───────────────────────────
    care_type = fields.Selection([
        ('child_headed', 'A Child Headed Household'),
        ('relatives', 'Living with Other Relatives / Adults'),
        ('alone', 'Child Living Alone'),
        ('interim', 'Interim Care Centre'),
        ('streets', 'Living on the streets'),
        ('other', 'Other'),
    ], string='Type of care arrangement')
    caregiver_name = fields.Char(string='Caregiver — Full Names')
    caregiver_tel = fields.Char(string='Caregiver — Telephone')
    care_institution = fields.Char(string='Institution Name')
    care_location = fields.Char(string='Region / District / Village / Camp')
    care_before = fields.Char(string='Care arrangement before')
    care_adequate = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Is the current care adequate / suitable for the child?')
    care_action_needed = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='If not, immediate action to find alternative care?')

    # ── protection concerns (tick all that apply) ────────────────────────
    concern_ids = fields.Many2many(
        'cp.protection.concern', 'cp_registration_concern_rel',
        'registration_id', 'concern_id', string='Protection Concerns')

    # ── immediate actions ────────────────────────────────────────────────
    action_ids = fields.One2many(
        'cp.registration.action', 'registration_id',
        string='Immediate Actions')
    rehab_action = fields.Text(
        string='Action for the rehabilitation centre')

    # ── D · data confidentiality ─────────────────────────────────────────
    withhold = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Does the Child want to withhold all or part of the '
              'information they have given from certain individuals / '
              'agencies?')
    withhold_what = fields.Char(
        string='Specify what information should be withheld')
    withhold_reason = fields.Char(string='Reasons for withholding information')
    withhold_family = fields.Boolean(string='Family')
    withhold_government = fields.Boolean(string='Government')
    withhold_nonstate = fields.Boolean(string='Non-state Actors')
    withhold_agencies = fields.Boolean(string='Other agencies')
    withhold_other = fields.Boolean(string='Other')
    next_followup_date = fields.Date(string='Date of the next follow-up visit')
    care_plan_date = fields.Date(
        string='Date Case Management Plan (Care Plan) will be finalised')

    # ── E · child protection / social worker officer ─────────────────────
    officer_name = fields.Char(string='Officer — Full Name')
    officer_position = fields.Char(string='Officer — Position')
    officer_agency = fields.Char(string='Officer — Agency')
    officer_date = fields.Date(string='Officer — Date')
    officer_location = fields.Char(
        string='Officer — Region / District / Village / Camp')
    officer_sign = fields.Char(string='Officer — Signature')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._advance_stage('verification')
        return records


class CpRegistrationAction(models.Model):
    """One row of the registration's 'immediate actions' table."""
    _name = 'cp.registration.action'
    _description = 'CP Registration Immediate Action'
    _order = 'sequence, id'

    registration_id = fields.Many2one(
        'cp.registration', string='Registration', required=True,
        ondelete='cascade')
    sequence = fields.Integer(string='No', default=10)
    action = fields.Char(string='Action Required')
    agency = fields.Char(string='If referral, specify agency')
    other_specify = fields.Char(string='If other, specify')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], string='Status', default='pending')
