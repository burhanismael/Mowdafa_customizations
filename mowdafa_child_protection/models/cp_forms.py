# -*- coding: utf-8 -*-
"""The managed track — cp.placement and the nine forms (CP-06..CP-15).

Each hangs off cp.case (daily & mentoring hang off the placement, not
the case, so a child in kinship care isn't nagged for records no one
can file). Partner records never carry any of these.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .cp_case import RECOMMENDATIONS


class CpFormMixin(models.AbstractModel):
    """Every CP form carries its own sequence reference and a chatter."""
    _name = 'cp.form.mixin'
    _description = 'CP Form Mixin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sequence_code = None

    name = fields.Char(
        string='Reference', readonly=True, copy=False, default='New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New' and self._sequence_code:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    self._sequence_code) or 'New'
        return super().create(vals_list)


class CpPlacement(models.Model):
    _name = 'cp.placement'
    _description = 'CP Placement'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.placement'
    _order = 'date_start desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade',
        domain=[('record_type', '=', 'managed')])
    type = fields.Selection([
        ('facility', 'Facility'),
        ('kinship', 'Kinship'),
        ('interim', 'Interim'),
        ('home', 'Home'),
    ], string='Type', required=True, default='facility')
    requires_daily = fields.Boolean(
        string='Requires Daily Record', compute='_compute_requires_daily',
        store=True,
        help='Daily records and mentoring only make sense where MOWDAFA '
             'staff see the child every day — facility placements.')
    date_start = fields.Date(
        string='Start Date', default=fields.Date.context_today)
    date_end = fields.Date(string='End Date')
    location = fields.Char(string='Location')
    notes = fields.Char(string='Notes')
    daily_record_ids = fields.One2many(
        'cp.daily.record', 'placement_id', string='Daily Records')
    mentoring_ids = fields.One2many(
        'cp.mentoring', 'placement_id', string='Mentoring')

    @api.depends('type')
    def _compute_requires_daily(self):
        for placement in self:
            placement.requires_daily = placement.type == 'facility'


class CpHandover(models.Model):
    """CP-06 — proves the ministry took custody of a child at a time
    from a named person. Cannot be saved without all four signatures."""
    _name = 'cp.handover'
    _description = 'CP Hand-over (CP-06)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.handover'
    _order = 'handover_datetime desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    handover_datetime = fields.Datetime(
        string='Date & Time', required=True, default=fields.Datetime.now)
    # handed over by
    by_organisation = fields.Char(string='Organisation')
    by_name = fields.Char(string='Full Name', required=True)
    by_position = fields.Char(string='Position')
    by_location = fields.Char(string='Location')
    by_contact = fields.Char(string='Contact')
    # handed over to / received by
    to_institution = fields.Char(
        string='Institution', default='MOWDAFA rehabilitation centre')
    received_by = fields.Char(string='Staff Name', required=True)
    received_role = fields.Char(string='Role')
    received_contact = fields.Char(string='Contact')
    received_address = fields.Char(string='Address')
    # signatures — all four required: the chain of custody
    sign_handing_over = fields.Char(
        string='Handing-over Signature', required=True)
    sign_child = fields.Char(
        string='Child Signature / Thumbprint', required=True)
    sign_receiver = fields.Char(
        string='Receiver Signature', required=True)
    sign_witness = fields.Char(
        string='Witness Signature', required=True)
    notes = fields.Char(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._advance_stage('registration')
        return records


class CpRegistration(models.Model):
    """CP-07/08 — the child becomes a person here: identity, two
    separate consents, and the withholding choices."""
    _name = 'cp.registration'
    _description = 'CP Registration (CP-07/08)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.registration'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    place = fields.Char(string='Place')
    date_of_arrival = fields.Date(string='Date of Arrival')
    registered_by = fields.Char(string='Registered By')
    # two consents, not one
    consent_registration = fields.Boolean(string='Consent to Registration')
    consent_registration_by = fields.Char(string='Given By')
    consent_data = fields.Boolean(string='Consent to Store & Share Data')
    consent_data_limits = fields.Char(string='Limits')
    child_assent = fields.Boolean(string="Child's Assent")
    # identity
    nickname = fields.Char(string='Nickname')
    father_name = fields.Char(string='Father')
    mother_name = fields.Char(string='Mother')
    other_relative = fields.Char(string='Other Relative')
    place_of_origin = fields.Char(string='Place of Origin')
    current_address = fields.Char(string='Current Address')
    # schooling
    schooling_history = fields.Char(string='Schooling History')
    literacy = fields.Char(string='Literacy')
    wants_to_learn = fields.Char(string='Wants to Learn')
    # identification & care
    found_at = fields.Char(string='Found / Brought From')
    referred_by = fields.Char(string='Referred By')
    care_before = fields.Char(string='Care Before')
    care_now = fields.Char(string='Care Now')
    immediate_actions = fields.Char(string='Immediate Actions')
    # confidentiality — withhold information
    withhold = fields.Boolean(string='Withhold Information?')
    withhold_what = fields.Char(string='What to Withhold')
    withhold_from = fields.Char(string='From Whom')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._advance_stage('verification')
        return records


class CpVerification(models.Model):
    """CP-09/10 — the claiming adult's account and the child's own,
    taken separately. Their agreement is computed on the case; where
    they disagree the file stops at the supervisor gate."""
    _name = 'cp.verification'
    _description = 'CP Verification (CP-09/10)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.verification'
    _order = 'interview_date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    kind = fields.Selection([
        ('adult', 'Adult — the claiming adult'),
        ('child', "Child — the child's own account"),
    ], string='Kind', required=True, default='adult')
    interview_date = fields.Date(
        string='Interviewed On', default=fields.Date.context_today)
    interview_place = fields.Char(string='Place')
    interviewed_alone = fields.Boolean(
        string='Interviewed Alone', default=True,
        help='The child is interviewed with no adult present.')
    # the adult (kind = adult)
    adult_name = fields.Char(string='Full Name')
    adult_relationship = fields.Char(string='Relationship')
    adult_contact = fields.Char(string='Contact')
    adult_address = fields.Char(string='Address')
    photo_recognised = fields.Boolean(string='Photo Recognised')
    account = fields.Text(
        string='Account',
        help='What was said — the other record is the check on it.')
    accounts_match = fields.Boolean(
        string='Accounts Match the File', default=True)
    child_wishes = fields.Char(string="Child's Wishes")
    recommendation = fields.Selection(
        RECOMMENDATIONS, string='Recommendation', required=True)
    reasons = fields.Text(string='Reasons')
    completed_by = fields.Char(string='Completed By')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._sync_verification()
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'recommendation' in vals or 'kind' in vals:
            self.case_id._sync_verification()
        return result


class CpDailyRecord(models.Model):
    """CP-11 — one per child per day, facility placements only.
    Fifteen seconds, or it won't happen."""
    _name = 'cp.daily.record'
    _description = 'CP Daily Record (CP-11)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.daily.record'
    _order = 'date desc, id desc'

    placement_id = fields.Many2one(
        'cp.placement', string='Placement', required=True,
        ondelete='cascade', domain=[('requires_daily', '=', True)])
    case_id = fields.Many2one(
        related='placement_id.case_id', store=True, string='Case')
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    attendance = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
    ], string='Attendance', default='present')
    hours = fields.Float(string='Hours')
    performance = fields.Selection([
        ('unsatisfactory', 'Unsatisfactory'),
        ('fair', 'Fair'),
        ('good', 'Good'),
        ('very_good', 'Very good'),
        ('outstanding', 'Outstanding'),
    ], string='Performance')
    events = fields.Char(
        string='Events',
        help='Sports, study circles, trips, LSBE, NFE, skill training…')
    comment = fields.Char(string="Supervisor's Comment")
    filed_by = fields.Many2one(
        'res.users', string='Filed By', default=lambda self: self.env.user)

    _sql_constraints = [
        ('placement_date_uniq', 'unique(placement_id, date)',
         'One daily record per child per day.'),
    ]


class CpMentoring(models.Model):
    """CP-12 — weekly, facility placements only. Last week's goals
    appear on this week's form: goals carry forward on their own."""
    _name = 'cp.mentoring'
    _description = 'CP Mentoring (CP-12)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.mentoring'
    _order = 'date desc, id desc'

    placement_id = fields.Many2one(
        'cp.placement', string='Placement', required=True,
        ondelete='cascade', domain=[('requires_daily', '=', True)])
    case_id = fields.Many2one(
        related='placement_id.case_id', store=True, string='Case')
    date = fields.Date(
        string='Week Of', required=True, default=fields.Date.context_today)
    mentor = fields.Char(string='Mentor')
    hours = fields.Float(string='Hours This Month')
    activities = fields.Char(
        string='Activities',
        help='Study circles, goal setting, sports, field trips, videos…')
    attended = fields.Boolean(string='Attended', default=True)
    goal_last_week = fields.Char(
        string='Goal Set Last Week',
        help='Carried forward from the previous session.')
    progress = fields.Selection([
        ('met', 'Met'),
        ('partly', 'Partly met'),
        ('carried', 'Carried over'),
    ], string='Progress')
    goal_next = fields.Char(string='Goal for Next Week')
    obstacles = fields.Text(string='Obstacles')
    for_staff = fields.Text(string='For Staff')

    @api.onchange('placement_id')
    def _onchange_placement_id(self):
        for session in self:
            if session.placement_id:
                last = self.search(
                    [('placement_id', '=', session.placement_id.id)],
                    order='date desc', limit=1)
                if last and last.goal_next:
                    session.goal_last_week = last.goal_next


class CpPsychosocial(models.Model):
    """CP-13 — as needed. A caseworker sees that the session took
    place and who ran it; the content is for the counsellor and
    supervisor only (the narrower rule wins)."""
    _name = 'cp.psychosocial'
    _description = 'CP Psychosocial Support (CP-13)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.psychosocial'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    date = fields.Date(
        string='Session Date', required=True,
        default=fields.Date.context_today)
    session_number = fields.Integer(string='Session #', default=1)
    counsellor = fields.Char(string='Counsellor')
    # restricted content — counsellor and supervisor only
    existing_illness = fields.Text(
        string='Existing Illness', groups='base.group_system')
    special_fears = fields.Text(
        string='Special Fears', groups='base.group_system')
    problems = fields.Text(
        string='Psychosocial Problems', groups='base.group_system')
    observation = fields.Text(
        string='Observation', groups='base.group_system')
    services_provided = fields.Text(
        string='Services Provided', groups='base.group_system')
    action_points = fields.Text(
        string='Action Points', groups='base.group_system')
    next_session = fields.Char(string='Next Session')


class CpReunification(models.Model):
    """CP-14 — opens only if the recommendation permits. The adult is
    carried in from the verification, not typed: a different name
    cannot quietly appear here."""
    _name = 'cp.reunification'
    _description = 'CP Reunification (CP-14)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.reunification'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    verified_adult = fields.Char(
        string='Verified Adult', compute='_compute_verified_adult',
        store=True, readonly=True,
        help='Carried in from the adult verification — not typed.')
    with_verified_adult = fields.Boolean(
        string='Reunified with the Verified Adult?', default=True)
    not_verified_reason = fields.Selection([
        ('change_of_mind', 'Change of mind'),
        ('death', 'Death of adult'),
        ('failed_verification', 'Failed verification'),
        ('other', 'Other'),
    ], string='If Not, Reason')
    tracing_type = fields.Selection([
        ('case_by_case', 'Case-by-case tracing'),
        ('mass', 'Mass tracing'),
        ('informal', 'Informal / spontaneous'),
        ('photo', 'Photo tracing'),
        ('mediation', 'Mediation'),
        ('other', 'Other'),
    ], string='How')
    additional_information = fields.Text(string='Additional Information')
    followup_needed = fields.Boolean(
        string='Follow-up Needed?', default=True)
    reintegration_priorities = fields.Text(string='Reintegration Priorities')
    completed_by = fields.Char(string='Completed By')
    adult_signature = fields.Char(string="Adult's Signature")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._advance_stage('reunification')
        return records

    @api.depends('case_id.verification_ids.adult_name',
                 'case_id.verification_ids.kind')
    def _compute_verified_adult(self):
        for record in self:
            adult = record.case_id.verification_ids.filtered(
                lambda v: v.kind == 'adult')[:1]
            record.verified_adult = adult.adult_name or False

    @api.constrains('with_verified_adult', 'not_verified_reason')
    def _check_reason(self):
        for record in self:
            if not record.with_verified_adult and not record.not_verified_reason:
                raise UserError(_(
                    'If the child did not go to the verified adult, the '
                    'reason must be picked from the list before the form '
                    'will save. A different name cannot quietly appear '
                    'here.'))


class CpFollowup(models.Model):
    """CP-15 — repeats; the case stays open while the child is home.
    The concerns listed at registration are the baseline every visit
    measures against."""
    _name = 'cp.followup'
    _description = 'CP Follow-up (CP-15)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.followup'
    _order = 'due_date, id'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    visit_number = fields.Integer(string='Visit #', default=1)
    due_date = fields.Date(string='Due')
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('done', 'Done'),
        ('overdue', 'Overdue'),
    ], string='Status', default='scheduled')
    visit_type = fields.Selection([
        ('after_reunification', 'After reunification'),
        ('interim_care', 'In interim care'),
    ], string='Type', default='after_reunification')
    child_seen = fields.Boolean(string='Child Seen?')
    same_caregiver = fields.Boolean(string='Same Caregiver?')
    caregiver = fields.Char(string='Caregiver')
    in_school = fields.Boolean(string='In School / Training?')
    school_detail = fields.Char(string='School Detail')
    concerns = fields.Text(
        string='Concerns',
        help='Measured against the registration baseline — a concern '
             'cannot be quietly dropped, only marked resolved.')
    visited_by = fields.Char(string='Visited By')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._advance_stage('followup')
        return records
