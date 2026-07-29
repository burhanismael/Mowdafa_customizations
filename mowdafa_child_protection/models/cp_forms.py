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
        'cp.case', string='Case', required=True, ondelete='cascade')
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
    by_contact = fields.Char(string='Handing-over Contact')
    # handed over to / received by
    to_institution = fields.Char(
        string='Institution', default='MOWDAFA rehabilitation centre')
    received_by = fields.Char(string='Staff Name', required=True)
    received_role = fields.Char(string='Role')
    received_contact = fields.Char(string='Receiver Contact')
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
    """CP-11 — Performance and Progress Record."""
    _name = 'cp.daily.record'
    _description = 'CP Performance and Progress Record (CP-11)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.daily.record'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    placement_id = fields.Many2one(
        'cp.placement', string='Placement', ondelete='set null',
        domain="[('case_id', '=', case_id)]")
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    week = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], string='Week')
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month')
    hours_attended = fields.Selection([
        ('36', '36 hrs./week'),
        ('42', '42 hrs./week'),
        ('49', '49 hrs./week'),
        ('56', '56 hrs./week'),
        ('63', '63 hrs./week'),
    ], string='Number of Hours Attended')
    event_ids = fields.Many2many(
        'cp.event.type', string='Number of Events Participated')
    performance_id = fields.Many2one(
        'cp.performance.rating', string='Overall Performance Rating',
        ondelete='restrict')
    comment = fields.Text(string="Supervisor's Comments")


MOTIVATION = [
    ('increased', 'Increased'),
    ('no_change', 'No Change'),
    ('decreased', 'Decreased'),
]

MOTIVATION_AREAS = [
    'Grades performance',
    'Session attendance',
    'Time management skills',
    'General attitude and outlook',
    'Self-esteem',
    'Confidence',
    'Communication with instructors/supervisors',
    'Willingness to accept responsibility',
]


class CpMentoring(models.Model):
    """CP-12 — the monthly Mentoring Activity Report: weekly attendance
    grid, hours, the activities the mentor and mentee did together and a
    motivation read across eight areas."""
    _name = 'cp.mentoring'
    _description = 'CP Mentoring Activity Report (CP-12)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.mentoring'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    placement_id = fields.Many2one(
        'cp.placement', string='Placement', ondelete='set null',
        domain="[('case_id', '=', case_id)]")
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    mentor = fields.Char(string='Mentor Name')
    mentor_phone = fields.Char(string='Phone')

    # 1 · weekly attendance / activity grid
    line_ids = fields.One2many(
        'cp.mentoring.line', 'mentoring_id', string='Weekly Activities')

    # 1 · total hours this month
    total_hours = fields.Selection([
        ('5', '5 hrs.'),
        ('7', '7 hrs.'),
        ('10', '10 hrs.'),
        ('15', '15 hrs.'),
    ], string='Total Hours This Month')

    # 2 · activities involved in this month (check all that apply)
    act_study_circles = fields.Boolean(string='Study circles')
    act_sports = fields.Boolean(string='Sports')
    act_field_trips = fields.Boolean(string='Field trips')
    act_watching_videos = fields.Boolean(string='Watching videos')
    act_goal_setting = fields.Boolean(string='Goal setting')
    act_pss = fields.Boolean(string='PSS')
    act_social = fields.Boolean(string='Social activities')
    act_other = fields.Boolean(string='Other')
    act_other_text = fields.Char(string='Other (describe)')

    # 3 · motivation this month (one row per area, pre-loaded)
    motivation_ids = fields.One2many(
        'cp.mentoring.motivation', 'mentoring_id', string='Motivation',
        default=lambda self: self._default_motivation())

    @api.model
    def _default_motivation(self):
        return [
            (0, 0, {'sequence': (i + 1) * 10, 'area': area})
            for i, area in enumerate(MOTIVATION_AREAS)
        ]

    # 4 & 5 · narrative
    obstacles = fields.Text(
        string='Major Obstacles',
        help='Describe any major obstacles in the relationship and how '
             'they were handled.')
    additional_comments = fields.Text(
        string='Additional Comments',
        help='Any additional comments, suggestions or questions for staff.')


class CpMentoringLine(models.Model):
    """One activity row of the mentoring report's weekly grid."""
    _name = 'cp.mentoring.line'
    _description = 'CP Mentoring Weekly Activity'
    _order = 'sequence, id'

    mentoring_id = fields.Many2one(
        'cp.mentoring', string='Mentoring Report', required=True,
        ondelete='cascade')
    sequence = fields.Integer(string='No', default=10)
    activity = fields.Char(string='Activity')
    week_1 = fields.Char(string='Week 1')
    week_2 = fields.Char(string='Week 2')
    week_3 = fields.Char(string='Week 3')
    week_4 = fields.Char(string='Week 4')
    week_5 = fields.Char(string='Week 5')


class CpMentoringMotivation(models.Model):
    """One motivation area of the mentoring report — pre-loaded with the
    eight standard areas so the mentor only picks the rating."""
    _name = 'cp.mentoring.motivation'
    _description = 'CP Mentoring Motivation'
    _order = 'sequence, id'

    mentoring_id = fields.Many2one(
        'cp.mentoring', string='Mentoring Report', required=True,
        ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    area = fields.Char(string='Activity')
    increased = fields.Char(string='Increased')
    no_change = fields.Char(string='No Change')
    decreased = fields.Char(string='Decreased')


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
        string='Date', required=True, default=fields.Date.context_today)

    # person identification
    person_name = fields.Char(string='Person Name')
    gender = fields.Selection(
        [('female', 'Female'), ('male', 'Male')], string='Gender')
    age = fields.Integer(string='Age')
    class_group = fields.Char(string='Class')

    # health & wellbeing — each a Yes/No with a describe box
    existing_illness = fields.Boolean(
        string='Existing Illness?', groups='base.group_system')
    existing_illness_desc = fields.Text(
        string='Describe (existing illness)', groups='base.group_system')
    previous_illness = fields.Boolean(
        string='Previous Serious Illness / Injury?',
        groups='base.group_system')
    previous_illness_desc = fields.Text(
        string='Describe (previous illness/injury)',
        groups='base.group_system')
    special_fears = fields.Boolean(
        string='Special Fears?', groups='base.group_system')
    special_fears_desc = fields.Text(
        string='Describe (special fears)', groups='base.group_system')
    psychosocial_problems = fields.Boolean(
        string='Psychosocial Problems?', groups='base.group_system')
    psychosocial_problems_desc = fields.Text(
        string='Describe (psychosocial problems)',
        groups='base.group_system')

    # observation
    play_with_others = fields.Text(
        string='Likes to do when playing with others',
        groups='base.group_system')
    play_alone = fields.Text(
        string='Likes to do when playing alone',
        groups='base.group_system')
    family_description = fields.Text(
        string='Family of the Person',
        help='Parents, siblings, grandparents and other extended family.',
        groups='base.group_system')

    # response
    additional_comments = fields.Text(
        string='Additional Comments', groups='base.group_system')
    services_provided = fields.Text(
        string='Services Provided (Area you advice)',
        groups='base.group_system')
    action_points = fields.Text(
        string='Action Points (Agreed points)', groups='base.group_system')

    @api.onchange('case_id')
    def _onchange_case_id_person(self):
        for record in self:
            case = record.case_id
            if case:
                record.person_name = case.child_name
                record.gender = case.sex
                record.age = case.age_years


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
