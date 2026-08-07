# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CpDailyRecord(models.Model):
    """CP-11 — Performance and Progress Record."""
    _name = 'cp.daily.record'
    _description = 'CP Performance and Progress Record (CP-11)'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.daily.record'
    _order = 'date desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    placement_id = fields.Many2one(
        'cp.placement', string='Placement', ondelete='set null',
        domain="[('case_id', '=', case_id)]")
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    week = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], string='Week')
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month')
    hours_attended = fields.Selection([
        ('36', '36 hrs./week'),
        ('42', '42 hrs./week'),
        ('49', '49 hrs./week'),
        ('56', '56 hrs./week'),
        ('63', '63 hrs./week'),
    ], string='Number of Hours Attended')
    event_ids = fields.Many2many(
        'cp.event.type', string='Number of Events Participated')
    performance_id = fields.Many2one(
        'cp.performance.rating', string='Overall Performance Rating',
        ondelete='restrict')
    comment = fields.Text(string="Supervisor's Comments")
