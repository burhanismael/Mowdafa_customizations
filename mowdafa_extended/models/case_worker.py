# -*- coding: utf-8 -*-
from odoo import models, fields, api


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
        string='ID',
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string='Code',
        compute='_compute_code',
        store=True,
        tracking=True,
    )

    @api.depends('institution', 'location', 'id_no')
    def _compute_code(self):
        for record in self:
            institution = (record.institution or '').strip().upper()
            location = (record.location or '').strip().upper()[:2]
            id_no = (record.id_no or '').strip()
            parts = [p for p in (institution, location, id_no) if p]
            record.code = '-'.join(parts)
