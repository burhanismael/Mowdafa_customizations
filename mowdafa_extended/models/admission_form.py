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
    survivor_id = fields.Many2one(
        'survivor.master',
        string='ID Number',
        required=True,
        tracking=True,
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
        compute='_compute_consent_count',
    )

    @api.depends('survivor_id')
    def _compute_consent_count(self):
        for record in self:
            record.consent_count = self.env['survivor.case'].search_count(
                [('survivor_id', '=', record.survivor_id.id)]
            ) if record.survivor_id else 0

    def action_view_consent_forms(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consent Forms',
            'res_model': 'survivor.case',
            'view_mode': 'tree,form',
            'domain': [('survivor_id', '=', self.survivor_id.id)],
            'context': {'default_survivor_id': self.survivor_id.id},
        }

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
