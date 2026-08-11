# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class CaseWorker(models.Model):
    _name = 'case.worker'
    _description = 'Case Worker'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'code'
    _rec_names_search = ['code', 'employee_id.name']
    _order = 'id desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        tracking=True,
    )
    institution = fields.Char(
        string='Institution/Organization',
        required=True,
        tracking=True,
    )
    location = fields.Char(
        string='Location',
        required=True,
        tracking=True,
    )
    id_no = fields.Char(
        string='ID No.',
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string='Code',
        compute='_compute_code',
        store=True,
        tracking=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
    ], string='Status', default='draft', required=True, tracking=True,
        copy=False)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_reset_draft(self):
        if not self.env.user.has_group(
                'mowdafa_extended.group_reset_to_draft'):
            raise AccessError(_(
                'Only users in the "Reset to Draft" group may unlock an '
                'active record.'))
        self.write({'state': 'draft'})

    @api.depends('institution', 'location', 'id_no')
    def _compute_code(self):
        for record in self:
            institution = (record.institution or '').strip().upper()
            location = (record.location or '').strip().upper()[:2]
            id_no = (record.id_no or '').strip()
            parts = [p for p in (institution, location, id_no) if p]
            record.code = '-'.join(parts)
