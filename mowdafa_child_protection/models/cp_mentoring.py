# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


MOTIVATION = [
    ('increased', 'Increased'),
    ('no_change', 'No Change'),
    ('decreased', 'Decreased'),
]


MOTIVATION_AREAS = [
    'Grades performance',
    'Session attendance',
    'Time management skills',
    'General attitude and outlook',
    'Self-esteem',
    'Confidence',
    'Communication with instructors/supervisors',
    'Willingness to accept responsibility',
]


class CpMentoring(models.Model):
    """CP-12 — the monthly Mentoring Activity Report: weekly attendance
    grid, hours, the activities the mentor and mentee did together and a
    motivation read across eight areas."""
    _name = 'cp.mentoring'
    _description = 'CP Mentoring Activity Report (CP-12)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.mentoring'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    placement_id = fields.Many2one(
        'cp.placement', string='Placement', ondelete='set null',
        domain="[('case_id', '=', case_id)]")
    child_full_name = fields.Char(
        related='case_id.child_name', string='Mentee')
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    mentor = fields.Char(string='Mentor Name')
    mentor_phone = fields.Char(string='Phone')

    # 1 · weekly attendance / activity grid
    line_ids = fields.One2many(
        'cp.mentoring.line', 'mentoring_id', string='Weekly Activities',
        default=lambda self: self._default_lines())

    @api.model
    def _default_lines(self):
        return [(0, 0, {'sequence': 10, 'activity': 'Session attendance'})]

    # 1 · total hours this month
    total_hours = fields.Selection([
        ('5', '5 hrs.'),
        ('7', '7 hrs.'),
        ('10', '10 hrs.'),
        ('15', '15 hrs.'),
    ], string='Total Hours This Month')

    # 2 · activities involved in this month (check all that apply)
    act_study_circles = fields.Boolean(string='Study circles')
    act_sports = fields.Boolean(string='Sports')
    act_field_trips = fields.Boolean(string='Field trips')
    act_watching_videos = fields.Boolean(string='Watching videos')
    act_goal_setting = fields.Boolean(string='Goal setting')
    act_pss = fields.Boolean(string='PSS')
    act_social = fields.Boolean(string='Social activities')
    act_other = fields.Boolean(string='Other')
    act_other_text = fields.Char(string='Other (describe)')

    # 3 · motivation this month (one row per area, pre-loaded)
    motivation_ids = fields.One2many(
        'cp.mentoring.motivation', 'mentoring_id', string='Motivation',
        default=lambda self: self._default_motivation())

    @api.model
    def _default_motivation(self):
        return [
            (0, 0, {'sequence': (i + 1) * 10, 'area': area})
            for i, area in enumerate(MOTIVATION_AREAS)
        ]

    # 4 & 5 · narrative
    obstacles = fields.Text(
        string='Major Obstacles',
        help='Describe any major obstacles in the relationship and how '
             'they were handled.')
    additional_comments = fields.Text(
        string='Additional Comments',
        help='Any additional comments, suggestions or questions for staff.')


class CpMentoringLine(models.Model):
    """One activity row of the mentoring report's weekly grid."""
    _name = 'cp.mentoring.line'
    _description = 'CP Mentoring Weekly Activity'
    _order = 'sequence, id'

    mentoring_id = fields.Many2one(
        'cp.mentoring', string='Mentoring Report', required=True,
        ondelete='cascade')
    sequence = fields.Integer(string='No', default=10)
    activity = fields.Char(string='Activity')
    week_1 = fields.Char(string='Week 1')
    week_2 = fields.Char(string='Week 2')
    week_3 = fields.Char(string='Week 3')
    week_4 = fields.Char(string='Week 4')
    week_5 = fields.Char(string='Week 5')


class CpMentoringMotivation(models.Model):
    """One motivation area of the mentoring report — pre-loaded with the
    eight standard areas so the mentor only picks the rating."""
    _name = 'cp.mentoring.motivation'
    _description = 'CP Mentoring Motivation'
    _order = 'sequence, id'

    mentoring_id = fields.Many2one(
        'cp.mentoring', string='Mentoring Report', required=True,
        ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    area = fields.Char(string='Activity')
    rating = fields.Selection(MOTIVATION, string='This Month')
