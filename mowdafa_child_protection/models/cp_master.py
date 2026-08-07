# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
        'cp.case', 'case_worker_id', string='Cases')
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


class CpSupervisor(models.Model):
    """Child Protection supervisor master — same shape as the GBV
    survivor.master: identified by name + mother's first name + birth
    date, with an auto-generated code."""
    _name = 'cp.supervisor'
    _description = 'CP Supervisor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'generated_code'
    _rec_names_search = ['generated_code', 'supervisor_name']
    _order = 'id desc'

    supervisor_name = fields.Char(
        string='Supervisor Name', required=True, tracking=True)
    photo = fields.Binary(string='Photo', attachment=True)
    mother_first_name = fields.Char(
        string="Mother's First Name", required=True, tracking=True)
    birth_date = fields.Date(string='Birth Date', required=True, tracking=True)
    birth_order = fields.Char(
        string='Birth Order (Digits)', required=True, tracking=True)
    place_of_birth = fields.Char(
        string='Place of Birth', required=True, tracking=True)
    generated_code = fields.Char(
        string='Generated Code', compute='_compute_generated_code',
        store=True, tracking=True)
    case_ids = fields.One2many(
        'cp.case', 'supervisor_id', string='Cases')
    case_count = fields.Integer(
        string='Cases', compute='_compute_case_count')

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

    @api.constrains('supervisor_name', 'mother_first_name', 'birth_date')
    def _check_unique_supervisor(self):
        for record in self:
            if not (record.supervisor_name and record.mother_first_name
                    and record.birth_date):
                continue
            duplicate = self.search([
                ('id', '!=', record.id),
                ('supervisor_name', '=ilike', record.supervisor_name.strip()),
                ('mother_first_name', '=ilike',
                 record.mother_first_name.strip()),
                ('birth_date', '=', record.birth_date),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    'A record with the same Name, Mother\'s First Name and '
                    'Birth Date already exists (%s).', duplicate.generated_code
                    or duplicate.supervisor_name))

    @api.model
    def _pad_birth_order(self, vals):
        birth_order = (vals.get('birth_order') or '').strip()
        if birth_order.isdigit() and len(birth_order) < 3:
            vals['birth_order'] = birth_order.zfill(3)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._pad_birth_order(vals)
        return super().create(vals_list)

    def write(self, vals):
        if 'birth_order' in vals:
            self._pad_birth_order(vals)
        return super().write(vals)

    @api.onchange('birth_order')
    def _onchange_birth_order(self):
        for record in self:
            birth_order = (record.birth_order or '').strip()
            if birth_order.isdigit() and len(birth_order) < 3:
                record.birth_order = birth_order.zfill(3)

    @api.depends('mother_first_name', 'birth_date',
                 'birth_order', 'place_of_birth')
    def _compute_generated_code(self):
        for record in self:
            birth_year = ''
            birth_month = ''
            if record.birth_date:
                birth_year = record.birth_date.strftime('%Y')
                birth_month = record.birth_date.strftime('%B')
            parts = [
                record.mother_first_name,
                birth_year,
                birth_month,
                record.birth_order,
                record.place_of_birth,
            ]
            code = ''
            for value in parts:
                value = (value or '').strip().upper()
                code += value[2] if len(value) >= 3 else ''
            record.generated_code = code


class CpPartnerAgency(models.Model):
    """The partner-record master: the agencies whose children MOWDAFA
    holds records for (UNICEF, Save the Children, GREDO, NRC, local
    CBOs…). Its own table, so the partner report's agency breakdown
    never depends on the general contacts directory."""
    _name = 'cp.partner.agency'
    _description = 'CP Partner Agency'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Agency', required=True, tracking=True)
    short_name = fields.Char(
        string='Short Name',
        help='Used in the deposited-records register, where the full '
             'agency name would not fit — e.g. "UNICEF" for "UNICEF — '
             'Child Protection sub-cluster".')
    code = fields.Char(string='Code')
    sector = fields.Char(
        string='Sector', help='e.g. Child Protection sub-cluster')
    focal_point_id = fields.Many2one(
        'case.worker', string='Caseworker', tracking=True,
        help='The agency\'s usual caseworker. Filled onto a new partner '
             'record automatically, and learned back from the first '
             'record that names one.')
    supervisor_id = fields.Many2one(
        'case.worker', string='Supervisor', tracking=True,
        help='Filled onto a new partner record automatically, and '
             'learned back from the first record that names one.')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That agency already exists.'),
    ]


class CpBasicNeed(models.Model):
    """Section 6 of the partner form lists basic needs as a multi-select
    (Food, Education, Psychosocial Support, Health Care, Legal Support,
    Other), so they are master data rather than free text — the partner
    report can then total them."""
    _name = 'cp.basic.need'
    _description = 'CP Basic Need'
    _order = 'sequence, id'

    name = fields.Char(string='Basic Need', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That basic need already exists.'),
    ]


class CpEventType(models.Model):
    """The events a child can take part in — Section 'Number of Events
    Participated' of the performance record. Master data, so the record
    ticks them as a multi-select and the report can total each."""
    _name = 'cp.event.type'
    _description = 'CP Event Type'
    _order = 'sequence, id'

    name = fields.Char(string='Event', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That event already exists.'),
    ]


class CpPerformanceRating(models.Model):
    """The Overall Performance Rating scale of the performance record —
    master data so the scale can be edited and the report can group by it."""
    _name = 'cp.performance.rating'
    _description = 'CP Performance Rating'
    _order = 'sequence, id'

    name = fields.Char(string='Rating', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That rating already exists.'),
    ]
