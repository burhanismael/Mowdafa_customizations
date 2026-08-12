# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from .cp_case import CONCERNS


class CpMinistryCase(models.Model):
    """A ministry case keyed on the same 12-section Puntland CP form as a
    partner-deposited record — its own master table, so MOWDAFA's own
    intake never blurs into what a partner sent.

    Same shape as ``cp.partner.record``, separate table and separate
    numbering (CPM/YYYY/NNNN).
    """
    _name = 'cp.ministry.case'
    _description = 'CP Ministry Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Case ID', readonly=True, copy=False, default='New',
        help='The MOWDAFA sequence number for this ministry case.')

    # ── record details ───────────────────────────────────────────────────
    date_received = fields.Date(
        string='Date Received', required=True,
        default=fields.Date.context_today, tracking=True)
    entered_by_id = fields.Many2one(
        'res.users', string='Entered By',
        default=lambda self: self.env.user, readonly=True)
    partner_worker_id = fields.Many2one(
        'case.worker', string='Caseworker')
    partner_supervisor_id = fields.Many2one(
        'case.worker', string='Supervisor')

    # ── 1 · child identification ─────────────────────────────────────────
    child_name = fields.Char(
        string='Full Name', required=True, tracking=True)
    preferred_name = fields.Char(string='Preferred Name')
    sex = fields.Selection(
        [('female', 'Female'), ('male', 'Male')],
        string='Sex', required=True, tracking=True)
    date_of_birth = fields.Date(string='Date of Birth')
    dob_estimated = fields.Boolean(string='DOB Estimated?')
    age_years = fields.Integer(string='Age (years)', required=True)
    nationality = fields.Char(string='Nationality', default='Somali')
    language = fields.Char(string='Language')
    population_group = fields.Selection([
        ('resident', 'Resident'),
        ('host', 'Host Community'),
        ('idp', 'IDP'),
        ('refugee', 'Refugee'),
        ('returnee', 'Returnee'),
        ('other', 'Other'),
    ], string='Population Group', required=True, tracking=True)
    disability = fields.Boolean(string='Disability')
    current_address = fields.Char(string="Child's Address")
    school_status = fields.Selection([
        ('yes', 'Yes — attending'),
        ('dropped_out', 'Dropped Out'),
        ('never', 'Never Attended'),
    ], string='School')
    school_name = fields.Char(string='School Name')

    # ── 2 · parent / caregiver ───────────────────────────────────────────
    caregiver_name = fields.Char(string='Caregiver')
    caregiver_relationship = fields.Char(string='Relationship')
    caregiver_phone = fields.Char(string='Telephone')
    caregiver_alt_contact = fields.Char(string='Alternative Contact')
    caregiver_address = fields.Char(string='Caregiver Address')
    living_arrangement = fields.Selection([
        ('both_parents', 'Both Parents'),
        ('mother', 'Mother'),
        ('father', 'Father'),
        ('extended_family', 'Extended Family'),
        ('alone', 'Alone'),
        ('institution', 'Institution'),
        ('other', 'Other'),
    ], string='Living Arrangement')

    # ── 3 · case identification & referral ───────────────────────────────
    region_id = fields.Many2one(
        'gbv.region', string='Region', required=True, tracking=True)
    district_id = fields.Many2one(
        'gbv.district', string='District', required=True, tracking=True,
        domain="[('region_id', '=?', region_id)]")
    date_identified = fields.Date(string='Date Identified')
    referral_source = fields.Selection([
        ('community', 'Community Member'),
        ('health', 'Health Facility'),
        ('ngo', 'NGO'),
        ('police', 'Police'),
        ('teacher', 'Teacher'),
        ('self', 'Self / Family'),
        ('other', 'Other'),
    ], string='Referral Source')
    referral_reason = fields.Text(string='Reason')

    # ── 4 · protection concern / 5 · safety & risk ───────────────────────
    protection_concern = fields.Selection(
        CONCERNS, string='Primary Concern', required=True, tracking=True)
    concern_description = fields.Text(string='Concern Description')
    risk_level = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('moderate', 'Moderate'),
        ('low', 'Low'),
    ], string='Risk Level', required=True, tracking=True)
    immediate_risk = fields.Boolean(string='Immediate Risk?')
    risk_factors = fields.Text(string='Risk Factors')
    protective_factors = fields.Text(string='Protective Factors')
    immediate_actions = fields.Text(string='Immediate Actions')

    # ── 6 · assessment of the situation ──────────────────────────────────
    child_views = fields.Text(string="Child's Views")
    family_situation = fields.Text(string='Family Situation')
    psychosocial_status = fields.Text(string='Psychosocial')
    health_status = fields.Char(string='Health')
    education_status = fields.Char(string='Education')
    basic_need_ids = fields.Many2many(
        'cp.basic.need', string='Basic Needs')

    # ── 7 · consent & assent ─────────────────────────────────────────────
    consent_explained = fields.Boolean(string='Process Explained')
    confidentiality_explained = fields.Boolean(
        string='Confidentiality Explained')
    caregiver_consent = fields.Boolean(string='Caregiver Consent')
    child_assent = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('na', 'N/A — too young'),
    ], string='Child Assent')
    consent_date = fields.Date(string='Consent Date')

    # ── 8 · best-interest assessment summary ─────────────────────────────
    key_findings = fields.Text(string='Key Findings')
    analysis = fields.Text(string='Analysis')
    interventions = fields.Text(string='Recommended Interventions')

    # ── 9 · case plan ─────────────────────────────────────────────────────
    plan_objective = fields.Char(string='Objective')
    plan_activities = fields.Text(string='Planned Activities')
    plan_responsible = fields.Char(string='Responsible Person')
    plan_target_date = fields.Date(string='Target Date')

    # ── 10 · referrals & services provided ───────────────────────────────
    services_health = fields.Char(string='Health Service')
    services_psychosocial = fields.Char(string='Psychosocial Service')
    services_education = fields.Char(string='Education Service')
    services_legal = fields.Char(string='Legal Service')
    services_tracing = fields.Char(string='Family Tracing')
    services_other = fields.Char(string='Other Services')

    # ── 11 · follow-up record ────────────────────────────────────────────
    followup_line_ids = fields.One2many(
        'cp.ministry.followup', 'record_id', string='Follow-up Record')

    # ── 12 · case closure ────────────────────────────────────────────────
    case_status = fields.Selection([
        ('open', 'Open'),
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ], string='Reported Status', required=True, default='open',
        tracking=True)
    last_followup_date = fields.Date(string='Last Follow-up')
    closure_date = fields.Date(string='Date Closed')
    closure_reason = fields.Text(string='Reason for Closure')
    closure_summary = fields.Text(string='Closure Summary')
    closure_situation = fields.Text(string="Child's Situation at Closure")
    closure_feedback = fields.Text(string='Family Feedback')
    closure_approved_date = fields.Date(string='Approved On')

    case_id = fields.Many2one(
        'cp.case', string='MOWDAFA Case', readonly=True, copy=False,
        help='Set when MOWDAFA opens a managed case from this record — '
             'the child has come into the ministry\'s care.')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    attachment_count = fields.Integer(
        compute='_compute_attachment_count', string='Documents')

    def _compute_attachment_count(self):
        counts = {}
        if self.ids:
            for res_id, count in self.env['ir.attachment']._read_group(
                    [('res_model', '=', 'cp.ministry.case'),
                     ('res_id', 'in', self.ids)],
                    groupby=['res_id'], aggregates=['__count']):
                counts[res_id] = count
        for record in self:
            record.attachment_count = counts.get(record.id, 0)

    def action_view_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', 'cp.ministry.case'),
                       ('res_id', '=', self.id)],
            'context': {'default_res_model': 'cp.ministry.case',
                        'default_res_id': self.id},
        }

    # ── opening a MOWDAFA case from this record ──────────────────────────
    def _concern_id(self):
        """This form keys the concern as a fixed selection; the case points
        at the master table. Match on the label, adding the entry the first
        time a concern is carried across."""
        self.ensure_one()
        label = dict(CONCERNS).get(self.protection_concern)
        if not label:
            return False
        Concern = self.env['cp.protection.concern'].sudo()
        concern = Concern.search([('name', '=', label)], limit=1)
        if not concern:
            concern = Concern.create({'name': label})
        return concern.id

    def _cp_directory_id(self, model, worker):
        """Agency staff live in the GBV ``case.worker`` directory, MOWDAFA's
        own in the CP ones. Carry the person over only when the same employee
        is already in the CP directory — never invent an entry there."""
        if not worker.employee_id:
            return False
        return self.env[model].search(
            [('employee_id', '=', worker.employee_id.id)], limit=1).id

    def _case_values(self):
        """The reporting spine both tracks share, carried across so the
        officer does not key the child twice."""
        self.ensure_one()
        source = dict(self._fields['referral_source'].selection or [])
        return {
            'child_name': self.child_name,
            'sex': self.sex,
            'date_of_birth': self.date_of_birth,
            'dob_estimated': self.dob_estimated,
            'age_years': self.age_years,
            'nationality': self.nationality,
            'population_group': self.population_group,
            'disability': self.disability,
            'region_id': self.region_id.id,
            'district_id': self.district_id.id,
            'date_identified': self.date_identified,
            'referral_source': source.get(self.referral_source) or '',
            'protection_concern_id': self._concern_id(),
            'concern_description': self.concern_description,
            'risk_level': self.risk_level,
            'immediate_risk': self.immediate_risk,
            'risk_factors': self.risk_factors,
            'case_worker_id': self._cp_directory_id(
                'cp.case.worker', self.partner_worker_id),
            'supervisor_id': self._cp_directory_id(
                'cp.supervisor', self.partner_supervisor_id),
        }

    def action_create_case(self):
        """The child has come into MOWDAFA's care: open a managed case from
        what is already recorded here. This record is kept as it was."""
        self.ensure_one()
        if self.case_id:
            return self.action_open_case()
        case = self.env['cp.case'].create(self._case_values())
        self.case_id = case.id
        case.message_post(body=_(
            'Opened from ministry case %s.', self.name))
        self.message_post(body=_(
            'MOWDAFA case %s opened from this record.', case.name))
        return self.action_open_case()

    def action_open_case(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('MOWDAFA Case'),
            'res_model': 'cp.case',
            'view_mode': 'form',
            'res_id': self.case_id.id,
            'target': 'current',
        }

    @api.depends('child_name', 'name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = '%s — %s' % (
                record.name, record.child_name or _('Not yet named'))

    @api.onchange('date_of_birth')
    def _onchange_date_of_birth(self):
        for record in self:
            if record.date_of_birth:
                today = fields.Date.context_today(record)
                record.age_years = max(
                    today.year - record.date_of_birth.year - (
                        (today.month, today.day) <
                        (record.date_of_birth.month, record.date_of_birth.day)),
                    0)

    @api.onchange('region_id')
    def _onchange_region_id(self):
        for record in self:
            if record.district_id and record.district_id.region_id != record.region_id:
                record.district_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'cp.ministry.case') or 'New'
        return super().create(vals_list)


class CpMinistryFollowup(models.Model):
    """Section 11 of the ministry case: the follow-up rows recorded against
    it — one line per visit."""
    _name = 'cp.ministry.followup'
    _description = 'CP Ministry Case Follow-up Line'
    _order = 'date desc, id desc'

    record_id = fields.Many2one(
        'cp.ministry.case', string='Ministry Case',
        required=True, ondelete='cascade')
    date = fields.Date(string='Date')
    progress = fields.Text(string='Progress')
    remaining_concerns = fields.Text(string='Remaining Concerns')
    next_actions = fields.Text(string='Next Actions')
