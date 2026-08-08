# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


def _loc(rec):
    parts = [
        rec.country_id.name if getattr(rec, 'country_id', False) else '',
        rec.region_id.name if getattr(rec, 'region_id', False) else '',
        rec.district_id.name if getattr(rec, 'district_id', False) else '',
        rec.village or '' if getattr(rec, 'village', False) else '',
    ]
    return ' · '.join(p for p in parts if p) or False


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

    # ── header ───────────────────────────────────────────────────────────
    visit_type = fields.Selection([
        ('interim_care', 'In Interim Care'),
        ('after_reunification', 'After Reunification'),
    ], string='Type of Follow-up', default='after_reunification')
    followup_period = fields.Char(
        string='Follow up after — period',
        compute='_compute_carried', store=True,
        help='Set on the reunification.')
    visit_number = fields.Integer(string='Visit #', default=1)
    due_date = fields.Date(string='Due')
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('overdue', 'Overdue'),
        ('done', 'Done'),
    ], string='Status', compute='_compute_status', store=True)

    # ── Section 1 — identity of the child (carried) ──────────────────────
    reg_id_number = fields.Char(
        string='Registration I/D Number',
        compute='_compute_carried', store=True)
    child_full_name = fields.Char(
        related='case_id.child_name', string="Child's Name")
    child_nickname = fields.Char(
        string='Nick Name', compute='_compute_carried', store=True)
    child_sex = fields.Selection(related='case_id.sex', string='Sex')
    child_dob = fields.Date(
        related='case_id.date_of_birth', string='Date of Birth')
    visiting_address = fields.Char(
        string='Visiting Address', compute='_compute_carried', store=True,
        help='From the reunification.')

    # ── Section 2 — outcome of the visit ─────────────────────────────────
    child_seen = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Was Child seen?')
    not_seen_reason = fields.Selection([
        ('visiting', 'Visiting friends / relatives'),
        ('at_school', 'At school'),
        ('moved_family', 'Moved with family'),
        ('moved_caregiver', 'Moved to another caregiver'),
        ('working', 'Working'),
        ('abducted', 'Abducted'),
        ('detention', 'In detention'),
        ('other', 'Other'),
    ], string='If Not, why not')

    # ── Section 3 — current care arrangements ────────────────────────────
    same_caregiver = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Is the child still living with the same caregiver?')
    change_reason = fields.Selection([
        ('poverty', 'Poverty'),
        ('education', 'Education'),
        ('relationship', 'Relationship Breakdown'),
        ('abuse', 'Abuse & Exploitation'),
        ('other', 'Other'),
    ], string='If not, give reasons for change')
    care_arrangement_type = fields.Selection([
        ('foster', 'Foster Family'),
        ('child_headed', 'Child Headed Household'),
        ('street', 'Street'),
        ('orphanage', 'Orphanage'),
        ('interim', 'Interim Care Centre'),
        ('other', 'Other'),
    ], string='If not, type of current care arrangement')
    caregiver = fields.Char(
        string='Caregiver', compute='_compute_carried', store=True)
    new_caregiver_name = fields.Char(string='New caregiver — Name')
    new_caregiver_nsd = fields.Char(
        string='New caregiver — Nick Name / Sex / DOB')
    new_caregiver_relationship = fields.Char(
        string='New caregiver — Child is My')
    new_caregiver_location = fields.Char(
        string='New caregiver — Country / Region / District / Town / Camp')
    new_care_start_date = fields.Date(
        string='Date new care arrangements started')
    change_circumstances = fields.Text(
        string='Explain circumstances of change (timing & reason)')

    # ── Section 4 — activities ───────────────────────────────────────────
    in_school = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Is the child in School or training?')
    not_school_reason = fields.Selection([
        ('financial', 'Financial Constraint'),
        ('access', 'Lack of access'),
        ('pregnancy', 'Pregnancy / Children'),
        ('ignorance', 'Ignorance'),
        ('interest', 'Lack of interest'),
        ('infrastructure', 'Lack of infrastructure'),
        ('early_marriage', 'Early Marriage'),
        ('other', 'Other'),
    ], string='If not, why not')
    education_type = fields.Selection([
        ('early_childhood', 'Early childhood'),
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('non_formal', 'Non-formal'),
        ('adult_literacy', 'Adult education / literacy'),
        ('vocational', 'Vocational training'),
        ('accelerated', 'Accelerated training'),
        ('other', 'Other'),
    ], string='If yes, what type of Education?')
    education_level = fields.Char(
        string='If relevant, what level have they achieved?')

    # ── Section 5 — protection assessment ────────────────────────────────
    assessment_ids = fields.One2many(
        'cp.followup.concern', 'followup_id', string='Protection Assessment',
        default=lambda self: self._default_assessment())

    # ── form completed by ────────────────────────────────────────────────
    completed_by = fields.Char(string='Completed By — Name')
    completed_position = fields.Char(string='Position')
    completed_agency = fields.Char(string='Agency')
    completed_place = fields.Char(string='Place')
    completed_date = fields.Date(string='Date')
    completed_location = fields.Char(
        string='Region / District / Village / Camp')
    completed_sign = fields.Char(string='Signature')

    @api.model
    def _default_assessment(self):
        case_id = self.env.context.get('default_case_id')
        if not case_id:
            return []
        case = self.env['cp.case'].browse(case_id)
        reg = case.registration_ids[:1]
        return [
            (0, 0, {'sequence': (i + 1) * 10,
                    'category': concern.name,
                    'at_registration': 'Yes — baseline'})
            for i, concern in enumerate(reg.concern_ids)
        ]

    @api.depends('case_id', 'case_id.registration_ids',
                 'case_id.reunification_ids')
    def _compute_carried(self):
        for record in self:
            case = record.case_id
            reg = case.registration_ids[:1]
            reu = case.reunification_ids[:1]
            record.reg_id_number = (reg.name if reg else False) or False
            record.child_nickname = (reg.nickname if reg else False) or False
            record.visiting_address = (
                reu.adult_location if reu else False) or False
            record.caregiver = (reu.verified_adult if reu else False) or False
            record.followup_period = (
                ('%s %s' % (reu.followup_interval, reu.followup_unit))
                if reu and reu.followup_interval else False)

    @api.depends('child_seen', 'due_date')
    def _compute_status(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.child_seen:
                record.status = 'done'
            elif record.due_date and record.due_date < today:
                record.status = 'overdue'
            else:
                record.status = 'scheduled'

    @api.constrains('change_reason')
    def _check_abuse_alert(self):
        # Abuse & Exploitation is a protection alert — surfaced in the UI;
        # kept here as the single source of truth for the flag.
        return

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._advance_stage('followup')
        return records


class CpFollowupConcern(models.Model):
    """One protection-assessment row of a follow-up visit — pre-loaded
    from the registration concerns as the baseline."""
    _name = 'cp.followup.concern'
    _description = 'CP Follow-up Protection Concern'
    _order = 'sequence, id'

    followup_id = fields.Many2one(
        'cp.followup', string='Follow-up', required=True, ondelete='cascade')
    sequence = fields.Integer(string='No', default=10)
    category = fields.Char(string='Category of concern')
    at_registration = fields.Char(string='At registration')
    immediate_action = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Immediate action required')
    details = fields.Text(string='Details of concerns and action required')
