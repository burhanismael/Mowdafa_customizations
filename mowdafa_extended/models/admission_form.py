# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AdmissionForm(models.Model):
    _name = 'admission.form'
    _description = 'Admission Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'file_no'
    _order = 'date desc, id desc'

    file_no = fields.Char(
        string='File No',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    consent_form_id = fields.Many2one(
        'survivor.case',
        string='Consent Form',
        tracking=True,
        copy=False,
    )
    survivor_id = fields.Many2one(
        'survivor.master',
        string='ID Number',
        required=True,
        tracking=True,
        copy=False,
    )
    date_of_birth = fields.Date(string='Date of Birth', tracking=True)
    age = fields.Char(string='Age/Estimate Age', tracking=True)
    cellphone_number = fields.Char(string='Cellphone Number', tracking=True)

    date_of_arrival = fields.Date(string='Date of Arrival', tracking=True)
    time_of_arrival = fields.Float(string='Time of Arrival')
    total_admitting = fields.Integer(
        string='Total Admitting (if accompanied by children)',
    )
    child_ids = fields.One2many(
        'admission.form.child',
        'admission_id',
        string='Children',
        copy=False,
    )
    last_permanent_address = fields.Char(string='Last Permanent Address')

    # If Employed
    company_name = fields.Char(string='Name of Company/Organisation')
    company_address = fields.Char(string='Physical Address')
    company_phone = fields.Char(string='Telephone Number')

    # Referral Details
    referred_by = fields.Char(string='Referred By')
    referral_phone = fields.Char(string='Telephone')

    offered_shelter_before = fields.Boolean(
        string='Have you ever been offered shelter here before?',
    )
    skills_to_nurture = fields.Text(
        string='Do you have any skills you would like to nurture?',
    )

    # Emergency Contact
    emergency_surname = fields.Char(string='Surname')
    emergency_first_names = fields.Char(string='First Names')
    emergency_relationship = fields.Char(string='Relationship')
    emergency_address = fields.Char(string='Address')
    emergency_phone = fields.Char(string='Cell/Tel Number')

    # History of Abuse
    history_of_abuse = fields.Text(string='History of Abuse')
    injuries_sustained = fields.Text(
        string='Injuries Sustained in the Attack (if applicable)',
    )
    special_medical_needs = fields.Text(string='Any Special Medical Needs')

    # Signatures
    client_full_name = fields.Char(string="Client's Full Name")
    client_signature = fields.Binary(string="Client's Signature", copy=False)
    client_signature_date = fields.Date(string='Client Signature Date')
    staff_signature = fields.Binary(string="Admitting Staff's Signature", copy=False)
    staff_signature_date = fields.Date(string='Staff Signature Date')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('admitted', 'Confirmed'),
    ], string='Status', default='draft', tracking=True)
    consent_count = fields.Integer(
        string='Consent Forms',
        compute='_compute_related_counts',
    )
    action_plan_count = fields.Integer(compute='_compute_related_counts')
    followup_count = fields.Integer(compute='_compute_related_counts')
    referral_count = fields.Integer(compute='_compute_related_counts')
    closure_count = fields.Integer(compute='_compute_related_counts')

    @api.depends('survivor_id')
    def _compute_related_counts(self):
        for record in self:
            domain = [('survivor_id', '=', record.survivor_id.id)]
            if record.survivor_id:
                record.consent_count = self.env['survivor.case'].search_count(domain)
                record.action_plan_count = self.env['action.plan'].search_count(domain)
                record.followup_count = self.env['followup.form'].search_count(domain)
                record.referral_count = self.env['referral.form'].search_count(domain)
                record.closure_count = self.env['case.closure'].search_count(domain)
            else:
                record.consent_count = 0
                record.action_plan_count = 0
                record.followup_count = 0
                record.referral_count = 0
                record.closure_count = 0

    def _action_view_related(self, res_model, name):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': res_model,
            'view_mode': 'tree,form',
            'domain': [('survivor_id', '=', self.survivor_id.id)],
            'context': {'default_survivor_id': self.survivor_id.id},
        }

    def action_view_consent_forms(self):
        return self._action_view_related('survivor.case', 'Consent Forms')

    def action_view_action_plans(self):
        return self._action_view_related('action.plan', 'Action Plans')

    def action_view_followups(self):
        return self._action_view_related('followup.form', 'Follow-up Forms')

    def action_view_referrals(self):
        return self._action_view_related('referral.form', 'Referral Forms')

    def action_view_closures(self):
        return self._action_view_related('case.closure', 'Case Closures')

    @api.onchange('consent_form_id')
    def _onchange_consent_form_id(self):
        for record in self:
            if record.consent_form_id and record.consent_form_id.survivor_id:
                record.survivor_id = record.consent_form_id.survivor_id

    @api.onchange('survivor_id')
    def _onchange_survivor_id(self):
        for record in self:
            if record.survivor_id:
                record.date_of_birth = record.survivor_id.birth_date
                if record.survivor_id.birth_date:
                    today = fields.Date.context_today(record)
                    birth_date = record.survivor_id.birth_date
                    age = today.year - birth_date.year - (
                        (today.month, today.day) < (birth_date.month, birth_date.day))
                    record.age = str(age)
                else:
                    record.age = False
            else:
                record.date_of_birth = False
                record.age = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('file_no', 'New') == 'New':
                vals['file_no'] = self.env['ir.sequence'].next_by_code(
                    'admission.form') or 'New'
        return super().create(vals_list)

    def action_admit(self):
        self.write({'state': 'admitted'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class AdmissionFormChild(models.Model):
    _name = 'admission.form.child'
    _description = 'Admission Form Child'

    admission_id = fields.Many2one(
        'admission.form',
        string='Admission Form',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(string='Child Name', required=True)
    age = fields.Char(string='Age')
