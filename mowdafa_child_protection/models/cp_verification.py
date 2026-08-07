# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .cp_case import RECOMMENDATIONS


class CpVerification(models.Model):
    """CP-10 — the child's own account (adult account is its own model,
    cp.verification.adult). Their agreement is computed on the case;
    where they disagree the file stops at the supervisor gate."""
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
    ], string='Kind', required=True, default='child')
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
