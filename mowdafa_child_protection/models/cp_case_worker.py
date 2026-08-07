# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CpCaseWorker(models.Model):
    """Child Protection case workers master — same shape as the GBV
    case.worker directory, but its own table."""
    _name = 'cp.case.worker'
    _description = 'CP Case Worker'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'code'
    _rec_names_search = ['code', 'employee_id.name']
    _order = 'id desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, tracking=True)
    institution = fields.Char(
        string='Institution/Organization', required=True, tracking=True)
    location = fields.Char(string='Location', required=True, tracking=True)
    id_no = fields.Char(string='ID No.', required=True, tracking=True)
    code = fields.Char(
        string='Code', compute='_compute_code', store=True, tracking=True)
    case_ids = fields.One2many(
        'cp.case', 'case_worker_id', string='Linked Cases')
    case_count = fields.Integer(
        string='Cases', compute='_compute_case_count')

    @api.depends('institution', 'location', 'id_no')
    def _compute_code(self):
        for record in self:
            institution = (record.institution or '').strip().upper()
            location = (record.location or '').strip().upper()[:2]
            id_no = (record.id_no or '').strip()
            parts = [p for p in (institution, location, id_no) if p]
            record.code = '-'.join(parts)

    @api.depends('case_ids')
    def _compute_case_count(self):
        for record in self:
            record.case_count = len(record.case_ids)

    def action_view_cases(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cases'),
            'res_model': 'cp.case',
            'view_mode': 'tree,form',
            'domain': [('case_worker_id', '=', self.id)],
            'context': {'default_case_worker_id': self.id},
        }
