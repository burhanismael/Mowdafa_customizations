# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


def _loc(rec, country='country_id', region='region_id',
         district='district_id', village='village'):
    """Join Country · Region · District · Village into one display string."""
    parts = [
        (getattr(rec, country).name if getattr(rec, country, False) else ''),
        (getattr(rec, region).name if getattr(rec, region, False) else ''),
        (getattr(rec, district).name if getattr(rec, district, False) else ''),
        (getattr(rec, village) or ''),
    ]
    return ' · '.join(p for p in parts if p) or False


class CpReunification(models.Model):
    """CP-14 — opens only if the recommendation permits. The child and
    adult identities are carried in from the registration and the
    verifications, not typed: a different name cannot quietly appear."""
    _name = 'cp.reunification'
    _description = 'CP Reunification (CP-14)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.reunification'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')

    # ── Section 1 — identity of the child (carried) ──────────────────────
    registration_id = fields.Many2one(
        'cp.registration', string='Registration',
        compute='_compute_carried', store=True)
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
    child_adult_relationship = fields.Char(
        string='The adult is My', compute='_compute_carried', store=True)
    child_location = fields.Char(
        string='Country / Region / District / Town-Village / Camp',
        compute='_compute_carried', store=True)

    # ── Section 2 — identity of the adult (carried from verification) ────
    verified_adult = fields.Char(
        string='Verified Adult', compute='_compute_carried', store=True)
    adult_nickname = fields.Char(
        string='Nick Name', compute='_compute_carried', store=True)
    adult_sex = fields.Selection(
        [('female', 'Female'), ('male', 'Male')],
        string='Sex', compute='_compute_carried', store=True)
    adult_dob = fields.Date(
        string='Date of Birth', compute='_compute_carried', store=True)
    adult_child_relationship = fields.Char(
        string='The Child is My', compute='_compute_carried', store=True)
    adult_phone = fields.Char(
        string='Telephone number', compute='_compute_carried', store=True)
    adult_location = fields.Char(
        string='Country / Region / District / Town-Village / Camp',
        compute='_compute_carried', store=True,
        help='Where the child now lives.')
    directions_landmark = fields.Char(
        string='Directions / landmark for the follow-up visit')

    # ── Section 3 — details of reunification ─────────────────────────────
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    with_verified_adult = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Was the child reunified with the Verified Adult?',
        default='yes')
    not_verified_reason = fields.Selection([
        ('change_of_mind', 'Change of Mind'),
        ('death', 'Death of Adult'),
        ('failed_verification', 'Failed Verification'),
        ('other', 'Other'),
    ], string='If not, what was the reason for the change?')
    not_verified_reason_other = fields.Char(string='Other — please specify')
    reunification_type = fields.Selection([
        ('mass', 'Mass Tracing'),
        ('case_by_case', 'Case by case'),
        ('informal', 'Informal / Spontaneous'),
        ('photo', 'Photo Tracing'),
        ('mediation', 'Mediation'),
        ('other', 'Other'),
    ], string='What type of reunification?')
    reunification_type_other = fields.Char(string='Other — please specify')
    additional_information = fields.Text(
        string='Additional information about the reunification')

    # ── follow-up ────────────────────────────────────────────────────────
    followup_needed = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Is there a need for follow-up?', default='yes')
    followup_interval = fields.Integer(string='Follow up after — every')
    followup_unit = fields.Selection([
        ('days', 'days'), ('weeks', 'weeks'), ('months', 'months'),
    ], string='Unit', default='weeks')
    followup_visits_count = fields.Integer(
        string='Number of visits to schedule')
    reintegration_priorities = fields.Text(
        string='Priorities for reintegration support or follow-up')

    # ── Section 4 — form completed by ────────────────────────────────────
    completed_by = fields.Char(string='Completed By — Name')
    completed_position = fields.Char(string='Position')
    completed_agency = fields.Char(string='Agency')
    completed_place = fields.Char(string='Place')
    completed_sign = fields.Char(string='Signature')
    adult_signature = fields.Char(string="Adult's Signature")

    @api.depends(
        'case_id', 'case_id.child_name',
        'case_id.registration_ids', 'case_id.adult_verification_ids',
        'case_id.verification_ids',
        'case_id.adult_verification_ids.adult_name')
    def _compute_carried(self):
        for record in self:
            case = record.case_id
            reg = case.registration_ids[:1]
            adult = case.adult_verification_ids[:1]
            child_ver = case.verification_ids[:1]
            # child (from registration + child verification)
            record.registration_id = reg.id if reg else False
            record.reg_id_number = (reg.name if reg else False) or False
            record.child_nickname = (reg.nickname if reg else False) or False
            record.child_location = _loc(reg) if reg else False
            record.child_adult_relationship = (
                child_ver.adult_relationship if child_ver else False) or False
            # adult (from adult verification)
            record.verified_adult = (adult.adult_name if adult else False) or False
            record.adult_nickname = (
                adult.adult_nickname if adult else False) or False
            record.adult_sex = adult.adult_sex if adult else False
            record.adult_dob = adult.adult_dob if adult else False
            record.adult_child_relationship = (
                adult.relationship if adult else False) or False
            record.adult_phone = (
                adult.adult_contact if adult else False) or False
            record.adult_location = (
                adult.adult_location if adult else False) or False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._advance_stage('reunification')
        return records

    @api.constrains('with_verified_adult', 'not_verified_reason')
    def _check_reason(self):
        for record in self:
            if record.with_verified_adult == 'no' \
                    and not record.not_verified_reason:
                raise UserError(_(
                    'If the child did not go to the verified adult, the '
                    'reason must be picked from the list before the form '
                    'will save. A different name cannot quietly appear '
                    'here.'))
