# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CpPlacement(models.Model):
    _name = 'cp.placement'
    _description = 'CP Placement'
    _inherit = ['cp.form.mixin']
    _sequence_code = 'cp.placement'
    _order = 'date_start desc, id desc'

    case_id = fields.Many2one(
        'cp.case', string='Case', required=True, ondelete='cascade')
    type = fields.Selection([
        ('facility', 'Facility'),
        ('kinship', 'Kinship'),
        ('interim', 'Interim'),
        ('home', 'Home'),
    ], string='Type', required=True, default='facility')
    requires_daily = fields.Boolean(
        string='Requires Daily Record', compute='_compute_requires_daily',
        store=True,
        help='Daily records and mentoring only make sense where MOWDAFA '
             'staff see the child every day — facility placements.')
    date_start = fields.Date(
        string='Start Date', default=fields.Date.context_today)
    date_end = fields.Date(string='End Date')
    location = fields.Char(string='Location')
    notes = fields.Char(string='Notes')
    daily_record_ids = fields.One2many(
        'cp.daily.record', 'placement_id', string='Daily Records')
    mentoring_ids = fields.One2many(
        'cp.mentoring', 'placement_id', string='Mentoring')

    @api.depends('type')
    def _compute_requires_daily(self):
        for placement in self:
            placement.requires_daily = placement.type == 'facility'
