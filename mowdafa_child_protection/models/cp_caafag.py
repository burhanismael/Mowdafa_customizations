# -*- coding: utf-8 -*-
"""The CAAFAG track — the same shape as the street-children case and its
nine forms, but each model gets its own table, so the two registers never
blur. Prototype inheritance copies every field and method; only the
relational links are re-pointed at the CAAFAG variants."""
from odoo import models, fields, api
from odoo.exceptions import ValidationError


# ── the case ─────────────────────────────────────────────────────────────
class CpCaafagCase(models.Model):
    _name = 'cp.caafag.case'
    _inherit = 'cp.case'
    _description = 'CAAFAG Case'

    case_type = fields.Selection(default='caafag')

    placement_ids = fields.One2many(
        'cp.caafag.placement', 'case_id', string='Placements')
    handover_ids = fields.One2many(
        'cp.caafag.handover', 'case_id', string='Hand-overs')
    registration_ids = fields.One2many(
        'cp.caafag.registration', 'case_id', string='Registrations')
    verification_ids = fields.One2many(
        'cp.caafag.verification.child', 'case_id',
        string='Child Verifications')
    adult_verification_ids = fields.One2many(
        'cp.caafag.verification.adult', 'case_id',
        string='Adult Verifications')
    psychosocial_ids = fields.One2many(
        'cp.caafag.psychosocial', 'case_id', string='Psychosocial Sessions')
    daily_record_ids = fields.One2many(
        'cp.caafag.daily.record', 'case_id', string='Performance Records')
    mentoring_ids = fields.One2many(
        'cp.caafag.mentoring', 'case_id', string='Mentoring Reports')
    reunification_ids = fields.One2many(
        'cp.caafag.reunification', 'case_id', string='Reunifications')
    cp_followup_ids = fields.One2many(
        'cp.caafag.followup', 'case_id', string='Follow-up Visits')
    case_report_ids = fields.One2many(
        'cp.caafag.case.report', 'case_id', string='Case Reports')
    case_report_count = fields.Integer(
        string='Case Reports', compute='_compute_case_report_count')

    @api.depends('case_report_ids')
    def _compute_case_report_count(self):
        for case in self:
            case.case_report_count = len(case.case_report_ids)

    def action_create_case_report(self):
        return self._open_cp_form(
            'cp.caafag.case.report', 'Case Report',
            {'default_supervisor_id': self.supervisor_id.id})

    def action_view_case_reports(self):
        return self._view_cp_records(
            'cp.caafag.case.report', 'Case Reports', self.case_report_ids)

    intake_ids = fields.One2many(
        'cp.caafag.intake', 'case_id', string='Intake Forms')
    intake_count = fields.Integer(
        string='Intake Forms', compute='_compute_intake_count')

    @api.depends('intake_ids')
    def _compute_intake_count(self):
        for case in self:
            case.intake_count = len(case.intake_ids)

    def action_create_intake(self):
        return self._open_cp_form(
            'cp.caafag.intake', 'Client Intake Form',
            {'default_client_name': self.child_name,
             'default_gender': self.sex,
             'default_date_of_birth': self.date_of_birth,
             'default_country_id': self.country_id.id,
             'default_region_id': self.region_id.id,
             'default_district_id': self.district_id.id,
             'default_village': self.village})

    def action_view_intakes(self):
        return self._view_cp_records(
            'cp.caafag.intake', 'Client Intake Forms', self.intake_ids)

    _CAAFAG_FORM_MODELS = {
        'cp.placement': 'cp.caafag.placement',
        'cp.handover': 'cp.caafag.handover',
        'cp.registration': 'cp.caafag.registration',
        'cp.verification.child': 'cp.caafag.verification.child',
        'cp.verification.adult': 'cp.caafag.verification.adult',
        'cp.psychosocial': 'cp.caafag.psychosocial',
        'cp.daily.record': 'cp.caafag.daily.record',
        'cp.mentoring': 'cp.caafag.mentoring',
        'cp.reunification': 'cp.caafag.reunification',
        'cp.followup': 'cp.caafag.followup',
    }

    def _open_cp_form(self, model, name, extra_context=None):
        return super()._open_cp_form(
            self._CAAFAG_FORM_MODELS.get(model, model), name, extra_context)

    def _view_cp_records(self, model, name, records):
        return super()._view_cp_records(
            self._CAAFAG_FORM_MODELS.get(model, model), name, records)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'cp.caafag.case') or 'New'
        return super().create(vals_list)


# ── the nine forms + placements ──────────────────────────────────────────
class CpCaafagPlacement(models.Model):
    _name = 'cp.caafag.placement'
    _inherit = 'cp.placement'
    _description = 'CAAFAG Placement'
    _sequence_code = 'cp.caafag.placement'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')
    daily_record_ids = fields.One2many(
        'cp.caafag.daily.record', 'placement_id', string='Daily Records')
    mentoring_ids = fields.One2many(
        'cp.caafag.mentoring', 'placement_id', string='Mentoring')


class CpCaafagHandover(models.Model):
    _name = 'cp.caafag.handover'
    _inherit = 'cp.handover'
    _description = 'CAAFAG Hand-over (CP-06)'
    _sequence_code = 'cp.caafag.handover'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')


class CpCaafagRegistration(models.Model):
    _name = 'cp.caafag.registration'
    _inherit = 'cp.registration'
    _description = 'CAAFAG Registration (CP-07/08)'
    _sequence_code = 'cp.caafag.registration'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')
    action_ids = fields.One2many(
        'cp.caafag.registration.action', 'registration_id',
        string='Immediate Actions')
    care_location_ids = fields.One2many(
        'cp.caafag.registration.care.location', 'registration_id',
        string='Care Locations')
    concern_ids = fields.Many2many(
        'cp.protection.concern', 'cp_caafag_registration_concern_rel',
        'registration_id', 'concern_id', string='Protection Concerns')

    # ── centre enrolment (CAAFAG only) ───────────────────────────────────
    batch_id = fields.Many2one(
        'cp.caafag.batch', string='Batch',
        help='The centre batch this registration enrols into '
             '(Configuration → Batches).')
    skill_ids = fields.Many2many(
        'cp.caafag.skill', 'cp_caafag_registration_skill_rel',
        'registration_id', 'skill_id', string='Chosen vocational skills',
        help='A child can take more than one skill. Drives the Batch KPI '
             'report (Configuration → Vocational Skills).')
    skill_certified = fields.Boolean(
        string='Skill certified',
        help='The child was certified in the chosen vocational skill.')
    centre = fields.Char(string='Centre')
    entry_month = fields.Char(string='Entry month / year')
    education_level = fields.Char(string='Education level')
    emergency_contact = fields.Char(string='Emergency contact / phone')
    health_problems = fields.Char(
        string='Health problems',
        groups='mowdafa_child_protection.group_cp_protection_supervisor')
    on_medication = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='On medication?',
        groups='mowdafa_child_protection.group_cp_protection_supervisor')
    emergency_treatment_auth = fields.Boolean(
        string='Emergency medical-treatment authorisation',
        help='Parent authorises examination / treatment in an emergency.')

    # ── CAAFAG profile — Section 2 of the CAAFAG registration.
    #    Restricted to the Protection Supervisor group; field-level
    #    groups also exclude it from other users' exports. ──────────────
    _CAAFAG_GROUPS = 'mowdafa_child_protection.group_cp_protection_supervisor'
    force_type = fields.Selection([
        ('government', 'Government'),
        ('non_government', 'Non-government'),
    ], string='Armed force / group type', groups=_CAAFAG_GROUPS)
    group_name = fields.Char(string='Name of group', groups=_CAAFAG_GROUPS)
    military_unit = fields.Char(string='Military unit', groups=_CAAFAG_GROUPS)
    commander = fields.Char(string='Commander', groups=_CAAFAG_GROUPS)
    unit_location = fields.Char(
        string='Unit location', groups=_CAAFAG_GROUPS)
    clan = fields.Char(string='Clan / sub-clan', groups=_CAAFAG_GROUPS)
    landmarks = fields.Char(string='Landmarks', groups=_CAAFAG_GROUPS)
    recruit_status = fields.Selection([
        ('recruited', 'Recruited'),
        ('re_recruited', 'Re-recruited'),
    ], string='Recruit status', groups=_CAAFAG_GROUPS)
    recruitment_place = fields.Char(
        string='Place of recruitment', groups=_CAAFAG_GROUPS)
    date_joined = fields.Date(string='Date joined', groups=_CAAFAG_GROUPS)
    recruitment_process = fields.Selection([
        ('forced', 'Forced'),
        ('not_forced', 'Not forced'),
    ], string='Recruitment process', groups=_CAAFAG_GROUPS)
    reason_services = fields.Boolean(
        string='Lack of essential services', groups=_CAAFAG_GROUPS)
    reason_financial = fields.Boolean(
        string='Financial', groups=_CAAFAG_GROUPS)
    reason_family = fields.Boolean(
        string='Family problems / abuse', groups=_CAAFAG_GROUPS)
    reason_friends = fields.Boolean(
        string='Follow friends', groups=_CAAFAG_GROUPS)
    reason_beliefs = fields.Boolean(
        string='Fight for beliefs', groups=_CAAFAG_GROUPS)
    reason_defend = fields.Boolean(
        string='Defend self / family', groups=_CAAFAG_GROUPS)
    main_role = fields.Selection([
        ('commander', 'Commander / ranked'),
        ('combatant', 'Combatant'),
        ('non_combat', 'Non-combat (cook, guide, porter)'),
        ('sexual', 'Girlfriend / "wife" / forced sexual activity'),
        ('other', 'Other'),
    ], string='Main role', groups=_CAAFAG_GROUPS)
    weapon_used = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'), ('dont_know', "Don't know"),
    ], string='Owned / used a weapon?', groups=_CAAFAG_GROUPS)
    date_left = fields.Date(string='Date left', groups=_CAAFAG_GROUPS)
    still_associated = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Still associated?', groups=_CAAFAG_GROUPS)
    leave_how = fields.Char(
        string='How did the child leave?', groups=_CAAFAG_GROUPS)
    demobilisation_place = fields.Char(
        string='Demobilisation place', groups=_CAAFAG_GROUPS)
    release_papers = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'), ('dont_know', "Don't know"),
    ], string='Release papers served?', groups=_CAAFAG_GROUPS)
    wishes_after_release = fields.Text(
        string='Wishes after release', groups=_CAAFAG_GROUPS)


class CpCaafagRegistrationCareLocation(models.Model):
    _name = 'cp.caafag.registration.care.location'
    _inherit = 'cp.registration.care.location'
    _description = 'CAAFAG Registration Care Location'

    registration_id = fields.Many2one(
        'cp.caafag.registration', string='Registration',
        required=True, ondelete='cascade')


class CpCaafagRegistrationAction(models.Model):
    _name = 'cp.caafag.registration.action'
    _inherit = 'cp.registration.action'
    _description = 'CAAFAG Registration Immediate Action'

    registration_id = fields.Many2one(
        'cp.caafag.registration', string='Registration',
        required=True, ondelete='cascade')


class CpCaafagVerificationChild(models.Model):
    _name = 'cp.caafag.verification.child'
    _inherit = 'cp.verification.child'
    _description = 'CAAFAG Child Verification (CP-10)'
    _sequence_code = 'cp.caafag.verification'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')
    registration_id = fields.Many2one(
        'cp.caafag.registration', string='Registration',
        compute='_compute_registration_info', store=True)


class CpCaafagVerificationAdult(models.Model):
    _name = 'cp.caafag.verification.adult'
    _inherit = 'cp.verification.adult'
    _description = 'CAAFAG Adult Verification (CP-09)'
    _sequence_code = 'cp.caafag.verification'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')


class CpCaafagPsychosocial(models.Model):
    _name = 'cp.caafag.psychosocial'
    _inherit = 'cp.psychosocial'
    _description = 'CAAFAG Psychosocial Support (CP-13)'
    _sequence_code = 'cp.caafag.psychosocial'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')


class CpCaafagDailyRecord(models.Model):
    _name = 'cp.caafag.daily.record'
    _inherit = 'cp.daily.record'
    _description = 'CAAFAG Performance and Progress Record'
    _sequence_code = 'cp.caafag.daily.record'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')
    placement_id = fields.Many2one(
        'cp.caafag.placement', string='Placement')


class CpCaafagMentoring(models.Model):
    _name = 'cp.caafag.mentoring'
    _inherit = 'cp.mentoring'
    _description = 'CAAFAG Mentoring Activity Report'
    _sequence_code = 'cp.caafag.mentoring'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')
    placement_id = fields.Many2one(
        'cp.caafag.placement', string='Placement')
    line_ids = fields.One2many(
        'cp.caafag.mentoring.line', 'mentoring_id', string='Lines')
    motivation_ids = fields.One2many(
        'cp.caafag.mentoring.motivation', 'mentoring_id',
        string='Motivations')


class CpCaafagMentoringLine(models.Model):
    _name = 'cp.caafag.mentoring.line'
    _inherit = 'cp.mentoring.line'
    _description = 'CAAFAG Mentoring Line'

    mentoring_id = fields.Many2one(
        'cp.caafag.mentoring', string='Mentoring Report',
        required=True, ondelete='cascade')


class CpCaafagMentoringMotivation(models.Model):
    _name = 'cp.caafag.mentoring.motivation'
    _inherit = 'cp.mentoring.motivation'
    _description = 'CAAFAG Mentoring Motivation'

    mentoring_id = fields.Many2one(
        'cp.caafag.mentoring', string='Mentoring Report',
        required=True, ondelete='cascade')


class CpCaafagReunification(models.Model):
    _name = 'cp.caafag.reunification'
    _inherit = 'cp.reunification'
    _description = 'CAAFAG Reunification (CP-14)'
    _sequence_code = 'cp.caafag.reunification'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')
    registration_id = fields.Many2one(
        'cp.caafag.registration', string='Registration',
        compute='_compute_carried', store=True)


class CpCaafagFollowup(models.Model):
    _name = 'cp.caafag.followup'
    _inherit = 'cp.followup'
    _description = 'CAAFAG Follow-up (CP-15)'
    _sequence_code = 'cp.caafag.followup'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')
    assessment_ids = fields.One2many(
        'cp.caafag.followup.concern', 'followup_id',
        string='Protection Assessment',
        default=lambda self: self._default_assessment())
    new_caregiver_ids = fields.One2many(
        'cp.caafag.followup.new.caregiver', 'followup_id',
        string='New Caregivers')


class CpCaafagFollowupConcern(models.Model):
    _name = 'cp.caafag.followup.concern'
    _inherit = 'cp.followup.concern'
    _description = 'CAAFAG Follow-up Concern'

    followup_id = fields.Many2one(
        'cp.caafag.followup', string='Follow-up Visit',
        required=True, ondelete='cascade')


class CpCaafagFollowupNewCaregiver(models.Model):
    _name = 'cp.caafag.followup.new.caregiver'
    _inherit = 'cp.followup.new.caregiver'
    _description = 'CAAFAG Follow-up New Caregiver'

    followup_id = fields.Many2one(
        'cp.caafag.followup', string='Follow-up Visit',
        required=True, ondelete='cascade')


# ── case report (in-care incident) — CAAFAG only ─────────────────────────
class CpCaafagCaseReport(models.Model):
    """An in-care incident report: what happened, where in the centre,
    who else was involved, and how it was closed off."""
    _name = 'cp.caafag.case.report'
    _description = 'CAAFAG Case Report (Incident)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.caafag.case.report'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')

    # ── child basic info ─────────────────────────────────────────────────
    child_name = fields.Char(
        related='case_id.child_name', string='Name of Child')
    placement = fields.Selection(
        related='case_id.placement_type', string='Placement')
    supervisor_id = fields.Many2one(
        'cp.supervisor', string='Name of supervisor')
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)

    # ── name of site ─────────────────────────────────────────────────────
    site_sleep = fields.Boolean(string='Sleep section')
    site_education = fields.Boolean(string='Education section')
    site_eating = fields.Boolean(string='Eating section')
    site_trip = fields.Boolean(string='Trip / tour')
    site_sports = fields.Boolean(string='During sports')
    site_other = fields.Boolean(string='Other')

    # ── type of case ─────────────────────────────────────────────────────
    type_fight_person = fields.Boolean(string='Fight to another person')
    type_fight_supervisor = fields.Boolean(
        string='Fight to instructor / supervisor')
    type_refuse = fields.Boolean(string='Refuse orders and instructions')
    type_smoked = fields.Boolean(string='Smoked')
    type_injury = fields.Boolean(string='Injury to person')
    type_damage = fields.Boolean(string='Property damage')
    type_discrimination = fields.Boolean(string='Discrimination')
    type_other = fields.Boolean(string='Other miscellaneous action')

    # ── other child involved (restricted) ────────────────────────────────
    harmed_case_id = fields.Many2one(
        'cp.caafag.case', string='Child who was harmed',
        groups='mowdafa_child_protection.group_cp_protection_supervisor')
    notify_supervisor = fields.Boolean(
        string='Notify supervisor?',
        help='Set automatically when "Injury to person" is ticked.')

    @api.onchange('type_injury')
    def _onchange_type_injury(self):
        for record in self:
            if record.type_injury:
                record.notify_supervisor = True

    # ── actions taken & sign-off ─────────────────────────────────────────
    action_taken = fields.Selection([
        ('advice', 'Advice'),
        ('warning', 'Warning'),
        ('apology', 'Offer apology'),
        ('sign_form', 'Sign case form'),
    ], string='Action taken', default='advice')
    sign_child = fields.Binary(string='Signature of the Child')
    sign_supervisor = fields.Binary(string='Signature of the supervisor')


# ── batches (Configuration master) + the Batch KPI report data ───────────
class CpCaafagBatch(models.Model):
    """A centre batch (e.g. BC-2026-03 — Garowe Centre): the cohort a
    CAAFAG registration enrols into. The Batch KPI report prints from
    here."""
    _name = 'cp.caafag.batch'
    _description = 'CAAFAG Batch'
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Batch', required=True)
    centre = fields.Char(string='Centre')
    date_start = fields.Date(string='Started')
    date_end = fields.Date(string='Completed')
    duration = fields.Char(string='Duration', help='e.g. 6 months')
    metrics_recorded = fields.Boolean(
        string='Additional KPI figures verified',
        help='Enable after entering the batch figures below. Unverified figures print as a dash.')
    skills_count = fields.Integer(string='Skills offered')
    above_satisfactory_count = fields.Integer(string='Children above satisfactory')
    dropout_count = fields.Integer(string='Confirmed dropouts')
    attendance_month = fields.Integer(string='Attendance month', default=6)
    attendance_percent = fields.Float(string='Attendance (%)', digits=(5, 1))
    attendance_baseline_percent = fields.Float(
        string='First month attendance (%)', digits=(5, 1))
    active = fields.Boolean(string='Active', default=True)
    registration_ids = fields.One2many(
        'cp.caafag.registration', 'batch_id', string='Registrations')
    registration_count = fields.Integer(
        string='Enrolled', compute='_compute_registration_count')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That batch already exists.'),
    ]

    @api.depends('registration_ids')
    def _compute_registration_count(self):
        for batch in self:
            batch.registration_count = len(batch.registration_ids)

    @api.constrains('metrics_recorded', 'skills_count', 'above_satisfactory_count',
                    'dropout_count', 'attendance_month', 'attendance_percent',
                    'attendance_baseline_percent', 'registration_ids')
    def _check_kpi_metrics(self):
        for batch in self:
            if not batch.metrics_recorded:
                continue
            total = len(batch.registration_ids.mapped('case_id'))
            if (batch.skills_count < 0 or batch.attendance_month < 1
                    or not 0 <= batch.above_satisfactory_count <= total
                    or not 0 <= batch.dropout_count <= total
                    or not 0 <= batch.attendance_percent <= 100
                    or not 0 <= batch.attendance_baseline_percent <= 100):
                raise ValidationError(
                    'KPI counts must be non-negative and child counts cannot exceed '
                    'enrolment. Attendance must be between 0 and 100, and month at least 1.')

    def _kpi_data(self):
        """Everything the Batch KPI report prints, in one dict."""
        self.ensure_one()
        cases = self.registration_ids.mapped('case_id')
        total = len(cases)

        def pct(part, whole=None):
            whole = total if whole is None else whole
            return round(100.0 * part / whole, 1) if whole else 0.0

        boys = cases.filtered(lambda c: c.sex == 'male')
        girls = cases.filtered(lambda c: c.sex == 'female')
        ages = [c.age_years for c in cases if c.age_years]
        completed = cases.filtered(
            lambda c: c.stage in ('reunification', 'followup'))
        pss = cases.filtered(lambda c: c.psychosocial_ids)

        bands = [('6–9', 6, 9), ('10–12', 10, 12),
                 ('13–15', 13, 15), ('16–17', 16, 17)]
        age_rows = []
        for label, lo, hi in bands:
            band = cases.filtered(lambda c, lo=lo, hi=hi: lo <= c.age_years <= hi)
            age_rows.append({
                'label': label,
                'boys': len(band.filtered(lambda c: c.sex == 'male')),
                'girls': len(band.filtered(lambda c: c.sex == 'female')),
                'total': len(band),
                'pct': pct(len(band)),
                'completed': len(band.filtered(
                    lambda c: c.stage in ('reunification', 'followup'))),
            })

        other = cases.filtered(lambda c: not 6 <= c.age_years <= 17)
        if other:
            age_rows.append({
                'label': 'Other / unknown',
                'boys': len(other.filtered(lambda c: c.sex == 'male')),
                'girls': len(other.filtered(lambda c: c.sex == 'female')),
                'total': len(other), 'pct': pct(len(other)),
                'completed': len(other & completed),
            })

        def grouped(records, key):
            counts = {}
            for rec in records:
                label = key(rec) or 'Undefined'
                counts[label] = counts.get(label, 0) + 1
            rows = [{'label': k, 'count': v, 'pct': pct(v)}
                    for k, v in counts.items()]
            rows.sort(key=lambda r: r['count'], reverse=True)
            return rows

        regions = grouped(cases, lambda c: c.region_id.name)
        max_region = max([r['count'] for r in regions], default=1)

        # districts keep their region, so the district bars can wear the
        # region's colour and share one legend
        region_order = [r['label'] for r in regions]
        district_map = {}
        for case in cases:
            label = case.district_id.name or 'Undefined'
            entry = district_map.setdefault(
                label, {'count': 0,
                        'region': case.region_id.name or 'Undefined'})
            entry['count'] += 1
        districts = [{
            'label': label,
            'count': entry['count'],
            'pct': pct(entry['count']),
            'region': entry['region'],
            'color': (region_order.index(entry['region'])
                      if entry['region'] in region_order else 0),
        } for label, entry in district_map.items()]
        districts.sort(key=lambda r: -r['count'])
        max_district = max([r['count'] for r in districts], default=1)

        # region rows with their districts and sex split, for the table
        by_region = {}
        for case in cases:
            by_region.setdefault(
                case.region_id.name or 'Undefined', []).append(case)
        region_rows = []
        for label, recs in sorted(
                by_region.items(), key=lambda kv: -len(kv[1])):
            district_counts = {}
            for case in recs:
                district = case.district_id.name or 'Undefined'
                district_counts[district] = district_counts.get(district, 0) + 1
            region_rows.append({
                'label': label,
                'districts': ', '.join(
                    '%s (%s)' % (k, v) for k, v in sorted(
                        district_counts.items(), key=lambda kv: -kv[1])),
                'count': len(recs),
                'pct': pct(len(recs)),
                'boys': sum(1 for c in recs if c.sex == 'male'),
                'girls': sum(1 for c in recs if c.sex == 'female'),
            })

        # chosen vocational skill, grouped from the registrations
        by_skill = {}
        for reg in self.registration_ids:
            for skill in reg.skill_ids:
                by_skill.setdefault(skill.name, []).append(reg)
        skills = []
        for label, regs in sorted(
                by_skill.items(), key=lambda kv: -len(kv[1])):
            enrolled = len(regs)
            skill_cases = [r.case_id for r in regs]
            certified = sum(1 for r in regs if r.skill_certified)
            skills.append({
                'label': label,
                'enrolled': enrolled,
                'boys': sum(1 for c in skill_cases if c.sex == 'male'),
                'girls': sum(1 for c in skill_cases if c.sex == 'female'),
                'completed': sum(1 for c in skill_cases
                                 if c.stage in ('reunification', 'followup')),
                'certified': certified,
                'rate': int(round(100.0 * certified / enrolled))
                        if enrolled else 0,
            })
        max_skill = max([s['enrolled'] for s in skills], default=1)
        skill_enrolments = sum(s['enrolled'] for s in skills)
        skill_certified_total = sum(s['certified'] for s in skills)

        # education level on entry — the registration's highest grade,
        # kept in the master's pedagogical order
        edu_map = {}
        for reg in self.registration_ids:
            grade = reg.highest_grade_id
            key = grade.name if grade else 'Not recorded'
            entry = edu_map.setdefault(
                key, {'count': 0,
                      'seq': grade.sequence if grade else 9999})
            entry['count'] += 1
        edu_rows = [{
            'label': label,
            'count': entry['count'],
            'pct': pct(entry['count']),
        } for label, entry in sorted(
            edu_map.items(), key=lambda kv: kv[1]['seq'])]
        max_edu = max([r['count'] for r in edu_rows], default=1)
        edu_top = (max(edu_rows, key=lambda r: r['count'])
                   if edu_rows else False)

        return {
            'total': total,
            'boys': len(boys), 'boys_pct': pct(len(boys)),
            'girls': len(girls), 'girls_pct': pct(len(girls)),
            'avg_age': round(sum(ages) / len(ages), 1) if ages else 0,
            'completed': len(completed),
            'completed_pct': pct(len(completed)),
            'dropped': total - len(completed),
            'dropped_pct': pct(total - len(completed)),
            'pss': len(pss), 'pss_pct': pct(len(pss)),
            'regions': regions, 'max_region': max_region,
            'districts': districts, 'max_district': max_district,
            'region_count': len(regions), 'district_count': len(districts),
            'age_rows': age_rows,
            'chart_max': max(6, ((max(max(r['boys'], r['girls']) for r in age_rows) + 5) // 6) * 6),
            'region_rows': region_rows,
            'skills': skills, 'max_skill': max_skill,
            'skills_offered': len(skills),
            'skill_enrolments': skill_enrolments,
            'skill_certified_total': skill_certified_total,
            'edu_rows': edu_rows, 'max_edu': max_edu, 'edu_top': edu_top,
            'skill_rate_total': int(round(
                100.0 * skill_certified_total / skill_enrolments))
                if skill_enrolments else 0,
            'issued': fields.Date.context_today(self),
            'above_satisfactory_pct': pct(self.above_satisfactory_count),
            'dropout_pct': pct(self.dropout_count),
            'attendance_change': round(self.attendance_percent - self.attendance_baseline_percent, 1),
        }


class CpCaafagBatchReportWizard(models.TransientModel):
    """Pick a batch, print its KPI report."""
    _name = 'cp.caafag.batch.report.wizard'
    _description = 'CAAFAG Batch KPI Report Wizard'

    batch_id = fields.Many2one(
        'cp.caafag.batch', string='Batch', required=True)

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            'mowdafa_child_protection.action_report_cp_caafag_batch'
        ).report_action(self.batch_id)


class CpCaafagSkill(models.Model):
    """Master list of vocational skills a CAAFAG registration can choose;
    the Batch KPI report groups on it."""
    _name = 'cp.caafag.skill'
    _description = 'CAAFAG Vocational Skill'
    _order = 'sequence, id'

    name = fields.Char(string='Skill', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That skill already exists.'),
    ]


# ── client intake form (in-care) — CAAFAG only ───────────────────────────
class CpCaafagIntake(models.Model):
    """The client intake form: who the child is, why the service is
    sought, and the signed consent to keep it on file."""
    _name = 'cp.caafag.intake'
    _description = 'CAAFAG Client Intake Form'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.caafag.intake'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.caafag.case', string='Case', required=True, ondelete='cascade')

    # ── personal information ─────────────────────────────────────────────
    client_name = fields.Char(string='Name')
    gender = fields.Selection([
        ('male', 'Male'), ('female', 'Female'),
    ], string='Gender')
    email = fields.Char(string='E-Mail')
    phone = fields.Char(string='Phone')
    date_of_birth = fields.Date(string='Date of Birth')

    # ── location (from the case) ─────────────────────────────────────────
    country_id = fields.Many2one('res.country', string='Country')
    region_id = fields.Many2one('gbv.region', string='Region')
    district_id = fields.Many2one(
        'gbv.district', string='District',
        domain="[('region_id', '=?', region_id)]")
    village = fields.Char(string='Village / Section')

    # ── service request ──────────────────────────────────────────────────
    service_reason = fields.Text(
        string='What is the reason for seeking our services?')
    heard_about = fields.Char(string='How did you hear about us?')

    # ── signature ────────────────────────────────────────────────────────
    sign = fields.Char(string='Signature')
    sign_img = fields.Binary(string='Signature (drawn)')
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
