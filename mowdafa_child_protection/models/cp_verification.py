# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .cp_case import RECOMMENDATIONS


class CpVerificationChild(models.Model):
    """CP-10 — the child's own account, taken separately from the adult's
    (cp.verification.adult). Their agreement is computed on the case;
    where they disagree the file stops at the supervisor gate."""
    _name = 'cp.verification.child'
    _description = 'CP Child Verification (CP-10)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.verification'
    _order = 'interview_date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')

    # ── Section 1 — information about the child ──────────────────────────
    # linked registration — its data is shown here, not re-typed
    registration_id = fields.Many2one(
        'cp.registration', string='Registration',
        compute='_compute_registration_info', store=True)
    reg_id_number = fields.Char(
        string='Registration I/D Number',
        compute='_compute_registration_info', store=True)
    child_nickname = fields.Char(
        string='Nick Name', compute='_compute_registration_info', store=True)
    location = fields.Char(
        string='Country / Region / District / Town-Village / Camp',
        compute='_compute_registration_info', store=True)
    child_full_name = fields.Char(
        related='case_id.child_name', string="Child's Name")
    child_sex = fields.Selection(related='case_id.sex', string='Sex')
    child_dob = fields.Date(
        related='case_id.date_of_birth', string='Date of Birth')
    adult_relationship = fields.Char(string='The adult is My')
    interview_date = fields.Date(
        string='Interviewed On', default=fields.Date.context_today)
    interview_place = fields.Char(string='Place')
    interviewed_alone = fields.Boolean(
        string='Interviewed Alone', default=True,
        help='The child is interviewed with no adult present.')

    @api.depends('case_id', 'case_id.registration_ids')
    def _compute_registration_info(self):
        for rec in self:
            reg = rec.case_id.registration_ids[:1]
            rec.registration_id = reg.id if reg else False
            rec.reg_id_number = (reg.name if reg else False) or False
            rec.child_nickname = (reg.nickname if reg else False) or False
            if reg:
                parts = [
                    reg.country_id.name if reg.country_id else '',
                    reg.region_id.name if reg.region_id else '',
                    reg.district_id.name if reg.district_id else '',
                    reg.village or '',
                ]
                rec.location = ' · '.join(p for p in parts if p) or False
            else:
                rec.location = False

    # ── Section 2 — verification ─────────────────────────────────────────
    info_match = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Does the information on the Adult Verification Form match '
              "with the information on the child's file?")
    accent_check = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'), ('na', 'N/A — over 5'),
    ], string='Accent check performed',
        help='Children under 5 / recently separated.')
    match_ids = fields.One2many(
        'cp.verification.child.match', 'verification_id',
        string='Detail Comparison',
        default=lambda self: self._default_match())

    @api.model
    def _default_match(self):
        details = [
            "Child's name",
            "Father's name",
            "Mother's name",
            'Place lived before the streets',
        ]
        return [
            (0, 0, {'sequence': (i + 1) * 10, 'detail': d})
            for i, d in enumerate(details)
        ]

    # ── Section 3 — wishes of the child ──────────────────────────────────
    knows_adult = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Does the child know the adult requesting verification?')
    wishes_reunification = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Does the child wish to be reunified with that person?')
    reunification_refusal_reason = fields.Text(string='If not, why not?')
    wishes_to_know = fields.Text(
        string='Is there any information the child wishes to know about '
               'his / her family before reunification?')

    # ── Section 4 — recommendation (drives the case gate) ────────────────
    recommendation = fields.Selection(
        RECOMMENDATIONS,
        string='Do you recommend reunification, and if not what other action?',
        required=True)
    alternative_action = fields.Text(
        string='Give details of any alternative action recommended')
    reasons = fields.Text(
        string='Give reasons for the action you recommend')

    # ── Section 5 — form completed by ────────────────────────────────────
    completed_by = fields.Char(string='Completed By — Name')
    completed_position = fields.Char(string='Position')
    completed_agency = fields.Char(string='Agency')
    completed_place = fields.Char(string='Place')
    completed_date = fields.Date(string='Date')
    completed_sign = fields.Char(string='Signature')

    def action_view_registration(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registration'),
            'res_model': 'cp.registration',
            'view_mode': 'form',
            'res_id': self.registration_id.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._sync_verification()
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'recommendation' in vals:
            self.case_id._sync_verification()
        return result


class CpVerificationAdult(models.Model):
    """CP-09 — the claiming adult's account, taken separately from the
    child's own (cp.verification). Section 2 records the child's details
    as the adult remembers them, kept apart from the child's file — the
    comparison is the point of the form."""
    _name = 'cp.verification.adult'
    _description = 'CP Adult Verification (CP-09)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.verification'
    _order = 'interview_date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')

    # ── Section 1 — information about the adult ──────────────────────────
    adult_name = fields.Char(string='Full Name')
    adult_nickname = fields.Char(string='Nick Name')
    adult_sex = fields.Selection(
        [('female', 'Female'), ('male', 'Male')], string='Sex')
    adult_dob = fields.Date(string='Date of Birth')
    adult_dob_estimated = fields.Boolean(string='DOB Estimated?')
    interview_date = fields.Date(
        string='Interviewed On', default=fields.Date.context_today)
    relationship = fields.Char(string='Child is My')
    adult_contact = fields.Char(string='Contact')
    adult_location = fields.Char(
        string='Country / Region / District / Town-Village / Camp')
    interview_place = fields.Char(string='Place')

    # ── Section 2 — child's details, as stated by the adult ──────────────
    recognize = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Do you recognize the child from any of the photographs displayed?')
    recognize_reason = fields.Char(string='If not, why not?')
    father_name = fields.Char(string="Name of the child's father")
    father_alive = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Is he alive?')
    father_address = fields.Char(string='Current address of father')
    other_children_missing = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Are any other children missing?')
    other_children_names = fields.Char(string='Names (of missing children)')
    mother_name = fields.Char(string="Name of the child's Mother")
    mother_alive = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Is she alive?')
    mother_address = fields.Char(string='Current address of Mother')
    other_family = fields.Text(string='Names of other family members')
    lived_before = fields.Char(
        string='Where did the child live before living on the streets? '
               '(Country / Region / District / Town-Village / Camp)')
    identifying_info = fields.Text(
        string="Information about the child's life that would help identify "
               'the child')
    memorable_events = fields.Text(
        string='Important and unique events the child might remember')

    # ── Section 3 — circumstances of separation ──────────────────────────
    sep_date = fields.Char(string='Date of Separation')
    sep_place = fields.Char(
        string='Place of Separation '
               '(Country / Region / District / Town-Village / Camp)')
    sep_circumstances = fields.Text(
        string='Circumstances of separation (how the child became separated, '
               'who the child was with at the time)')
    sep_caregiver_address = fields.Char(
        string='Address of that person (alternative caregiver)')

    # ── Section 5 — agreement to take the child ──────────────────────────
    agreement_name = fields.Char(string='Agreement — Name')
    agreement_sign = fields.Char(string='Agreement — Signature')
    reunification_info = fields.Text(
        string='Information to help the child make an informed decision '
               'about reunification')
    want_child_live = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Do you want the child to come and live with you?')
    able_to_care = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Are you able to care for him / her / them?')
    other_caregiver_available = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='If not, is there any other family member who could take '
              'care of the child?')

    # ── Section 6 — form completed by ────────────────────────────────────
    completed_by = fields.Char(string='Completed By — Name')
    completed_position = fields.Char(string='Position')
    completed_agency = fields.Char(string='Agency')
    completed_date = fields.Date(string='Date')
    completed_place = fields.Char(string='Place')
    completed_sign = fields.Char(string='Signature')
    interviewed_alone = fields.Boolean(string='Interviewed Alone')

    # ── the verification decision (drives the case gate) ─────────────────
    recommendation = fields.Selection(
        RECOMMENDATIONS, string='Recommendation', required=True)
    reasons = fields.Text(string='Reasons')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.case_id._sync_verification()
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'recommendation' in vals:
            self.case_id._sync_verification()
        return result


class CpVerificationChildMatch(models.Model):
    """One comparison row of the child verification's Section 2 — a
    side-by-side of the adult's answer against the child's file."""
    _name = 'cp.verification.child.match'
    _description = 'CP Child Verification Match Line'
    _order = 'sequence, id'

    verification_id = fields.Many2one(
        'cp.verification.child', string='Child Verification',
        required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    detail = fields.Char(string='Detail from the Adult Verification Form')
    adult_answer = fields.Char(string="Adult's answer")
    child_file = fields.Char(string="Child's file")
    match = fields.Boolean(string='Match')
