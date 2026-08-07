# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
