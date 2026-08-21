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

    def init(self):
        """The GBV access groups/rules were first installed inside a
        noupdate block; clear the flag so the renamed groups and the
        GBV Access category in gbv_security.xml apply on upgrade."""
        self.env.cr.execute("""
            UPDATE ir_model_data SET noupdate = false
            WHERE module = 'mowdafa_extended'
              AND (name IN ('group_gbv_case_worker', 'group_gbv_manager',
                            'module_category_gbv_access')
                   OR name LIKE 'rule\\_%')
        """)

    @api.model
    def _default_for_user(self):
        """The caseworker record of the logged-in user, active preferred."""
        domain = [('employee_id.user_id', '=', self.env.uid)]
        return (self.search(domain + [('state', '=', 'active')], limit=1)
                or self.search(domain, limit=1))

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
