# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
