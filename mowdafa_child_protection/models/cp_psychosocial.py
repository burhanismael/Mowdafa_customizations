# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
