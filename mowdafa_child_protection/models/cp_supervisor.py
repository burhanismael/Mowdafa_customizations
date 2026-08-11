# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class CpSupervisor(models.Model):
    """Child Protection supervisor master — an employee, the organization
    they answer to and their ID number, activated once the entry is
    checked."""
    _name = 'cp.supervisor'
    _description = 'CP Supervisor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'
    _rec_names_search = ['employee_id.name', 'id_no', 'institution']
    _order = 'id desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, tracking=True)
    institution = fields.Char(
        string='Institution/Organization', required=True, tracking=True)
    id_no = fields.Char(string='ID No.', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
    ], string='Status', default='draft', required=True, tracking=True,
        copy=False)
    case_ids = fields.One2many(
        'cp.case', 'supervisor_id', string='Linked Cases')
    case_count = fields.Integer(
        string='Cases', compute='_compute_case_count')

    def action_activate(self):
        self.write({'state': 'active'})

    def action_reset_draft(self):
        if not self.env.user.has_group(
                'mowdafa_extended.group_reset_to_draft'):
            raise AccessError(_(
                'Only users in the "Reset to Draft" group may unlock an '
                'active record.'))
        self.write({'state': 'draft'})

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
            'domain': [('supervisor_id', '=', self.id)],
            'context': {'default_supervisor_id': self.id},
        }
