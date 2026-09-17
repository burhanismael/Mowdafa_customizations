# -*- coding: utf-8 -*-
"""The CAAFAG track — the same shape as the street-children case and its
nine forms, but each model gets its own table, so the two registers never
blur. Prototype inheritance copies every field and method; only the
relational links are re-pointed at the CAAFAG variants."""
from odoo import models, fields, api


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
    concern_ids = fields.Many2many(
        'cp.protection.concern', 'cp_caafag_registration_concern_rel',
        'registration_id', 'concern_id', string='Protection Concerns')

    # ── centre enrolment (CAAFAG only) ───────────────────────────────────
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
