# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
    direction = fields.Selection([
        ('handed_over', 'Handed over to MOWDAFA'),
        ('received', 'Received from MOWDAFA'),
    ], string='This form certifies that a child was',
        default='handed_over', required=True)

    # ── child summary (read from the case, for the header) ───────────────
    child_full_name = fields.Char(
        related='case_id.child_name', string='Child Full Name',
        readonly=False)
    child_sex = fields.Selection(
        related='case_id.sex', string='Sex')
    child_dob = fields.Date(
        related='case_id.date_of_birth', string='Date of Birth')
    child_dob_estimated = fields.Boolean(
        related='case_id.dob_estimated', string='DOB Estimated?')
    child_father = fields.Char(
        related='case_id.middle_name', string="Father's Name")
    child_nationality = fields.Char(
        related='case_id.nationality', string='Nationality')

    # handed over by
    by_organisation = fields.Char(string='Organisation')
    by_name = fields.Char(string='Full Name', required=True)
    by_position = fields.Char(string='Position / Title')
    by_location = fields.Char(string='Location')
    by_contact = fields.Char(string='Handing-over Contact')
    # handed over to / received by
    to_institution = fields.Char(string='Institution / Location')
    handed_to_type = fields.Selection([
        ('family', 'Family'),
        ('institution', 'Institution'),
        ('other', 'Other'),
    ], string='Child was handed over to', default='institution')
    handed_to_other = fields.Char(string='If Other, specify')
    received_by = fields.Char(
        string='Name of MOWDAFA staff / family member', required=True)
    received_role = fields.Char(string='Role')
    received_contact = fields.Char(string='Receiver Contact')
    received_address = fields.Char(string='Complete Address')
    child_title = fields.Char(string='Child Title')
    witness_name = fields.Char(string='Witness Name')
    witness_role = fields.Char(string='Witness Title')
    sign_date = fields.Date(
        string='Signature Date', default=fields.Date.context_today)
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
