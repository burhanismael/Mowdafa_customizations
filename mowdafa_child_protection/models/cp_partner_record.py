# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from .cp_case import CONCERNS


class CpPartnerRecord(models.Model):
    """A record a partner agency deposited: the 12-section Puntland CP
    form, keyed verbatim by a MOWDAFA records officer from whatever
    files the partner sent (scan, spreadsheet, photo, email).

    Its own master table (CP-16/17) — never a cp.case. The partner
    keeps the child and does the work; MOWDAFA only stores and reports
    on this. No pipeline, no gate, no rhythm, no photo.
    """
    _name = 'cp.partner.record'
    _description = 'CP Partner Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Case ID', readonly=True, copy=False, default='New',
        help="The partner's own Case ID, kept verbatim, becomes the "
             "record's reference. Falls back to a MOWDAFA sequence if "
             "the partner did not give one.")

    # ── provenance — who sent it ─────────────────────────────────────────
    partner_agency_id = fields.Many2one(
        'cp.partner.agency', string='Partner Agency',
        required=True, tracking=True)
    partner_case_id = fields.Char(
        string='Partner Case ID', copy=False,
        help="The partner's own identifier, kept verbatim.")
    date_received = fields.Date(
        string='Date Received', required=True,
        default=fields.Date.context_today, tracking=True)
    entered_by_id = fields.Many2one(
        'res.users', string='Entered By',
        default=lambda self: self.env.user, readonly=True)
    partner_short_name = fields.Char(
        string='Partner', compute='_compute_partner_short_name', store=True)
    partner_worker_id = fields.Many2one(
        'case.worker', string='Caseworker',
        help='Filled from the agency when it names a usual caseworker; '
             'pick one it does not know and the agency learns it back.')
    partner_supervisor_id = fields.Many2one(
        'case.worker', string='Supervisor')
    agency_sector = fields.Char(
        related='partner_agency_id.sector', string='Sector', readonly=True)
    agency_phone = fields.Char(
        related='partner_agency_id.phone', string='Agency Phone', readonly=True)
    agency_email = fields.Char(
        related='partner_agency_id.email', string='Agency Email', readonly=True)

    @api.depends('partner_agency_id.short_name', 'partner_agency_id.name')
    def _compute_partner_short_name(self):
        for record in self:
            agency = record.partner_agency_id
            record.partner_short_name = agency.short_name or agency.name or ''

    # ── 1 · child identification ─────────────────────────────────────────
    child_name = fields.Char(
        string='Full Name', required=True, tracking=True)
    preferred_name = fields.Char(string='Preferred Name')
    sex = fields.Selection(
        [('female', 'Female'), ('male', 'Male')],
        string='Sex', required=True, tracking=True)
    date_of_birth = fields.Date(string='Date of Birth')
    dob_estimated = fields.Boolean(string='DOB Estimated?')
    age_years = fields.Integer(string='Age (years)', required=True)
    nationality = fields.Char(string='Nationality', default='Somali')
    language = fields.Char(string='Language')
    population_group = fields.Selection([
        ('resident', 'Resident'),
        ('host', 'Host Community'),
        ('idp', 'IDP'),
        ('refugee', 'Refugee'),
        ('returnee', 'Returnee'),
        ('other', 'Other'),
    ], string='Population Group', required=True, tracking=True)
    disability = fields.Boolean(string='Disability')
    current_address = fields.Char(string="Child's Address")
    school_status = fields.Selection([
        ('yes', 'Yes — attending'),
        ('dropped_out', 'Dropped Out'),
        ('never', 'Never Attended'),
    ], string='School')
    school_name = fields.Char(string='School Name')

    # ── 2 · parent / caregiver ───────────────────────────────────────────
    caregiver_name = fields.Char(string='Caregiver')
    caregiver_relationship = fields.Char(string='Relationship')
    caregiver_phone = fields.Char(string='Telephone')
    caregiver_alt_contact = fields.Char(string='Alternative Contact')
    caregiver_address = fields.Char(string='Caregiver Address')
    living_arrangement = fields.Selection([
        ('both_parents', 'Both Parents'),
        ('mother', 'Mother'),
        ('father', 'Father'),
        ('extended_family', 'Extended Family'),
        ('alone', 'Alone'),
        ('institution', 'Institution'),
        ('other', 'Other'),
    ], string='Living Arrangement')

    # ── 3 · case identification & referral ───────────────────────────────
    region_id = fields.Many2one(
        'gbv.region', string='Region', required=True, tracking=True)
    district_id = fields.Many2one(
        'gbv.district', string='District', required=True, tracking=True,
        domain="[('region_id', '=?', region_id)]")
    date_identified = fields.Date(string='Date Identified')
    referral_source = fields.Selection([
        ('community', 'Community Member'),
        ('health', 'Health Facility'),
        ('ngo', 'NGO'),
        ('police', 'Police'),
        ('teacher', 'Teacher'),
        ('self', 'Self / Family'),
        ('other', 'Other'),
    ], string='Referral Source')
    referral_reason = fields.Text(string='Reason')

    # ── 4 · protection concern / 5 · safety & risk ───────────────────────
    protection_concern = fields.Selection(
        CONCERNS, string='Primary Concern', required=True, tracking=True)
    concern_description = fields.Text(string='Concern Description')
    risk_level = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('moderate', 'Moderate'),
        ('low', 'Low'),
    ], string='Risk Level', required=True, tracking=True)
    immediate_risk = fields.Boolean(string='Immediate Risk?')
    risk_factors = fields.Text(string='Risk Factors')
    protective_factors = fields.Text(string='Protective Factors')
    immediate_actions = fields.Text(string='Immediate Actions')

    # ── 6 · assessment of the situation ──────────────────────────────────
    child_views = fields.Text(string="Child's Views")
    family_situation = fields.Text(string='Family Situation')
    psychosocial_status = fields.Text(string='Psychosocial')
    health_status = fields.Char(string='Health')
    education_status = fields.Char(string='Education')
    basic_need_ids = fields.Many2many(
        'cp.basic.need', string='Basic Needs')

    # ── 7 · consent & assent (as the partner recorded) ───────────────────
    consent_explained = fields.Boolean(string='Process Explained')
    confidentiality_explained = fields.Boolean(
        string='Confidentiality Explained')
    caregiver_consent = fields.Boolean(string='Caregiver Consent')
    child_assent = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('na', 'N/A — too young'),
    ], string='Child Assent')
    consent_date = fields.Date(string='Consent Date')

    # ── 8 · best-interest assessment summary ─────────────────────────────
    key_findings = fields.Text(string='Key Findings')
    analysis = fields.Text(string='Analysis')
    interventions = fields.Text(string='Recommended Interventions')

    # ── 9 · case plan ─────────────────────────────────────────────────────
    plan_objective = fields.Char(string='Objective')
    plan_activities = fields.Text(string='Planned Activities')
    plan_responsible = fields.Char(string='Responsible Person')
    plan_target_date = fields.Date(string='Target Date')

    # ── 10 · referrals & services provided ───────────────────────────────
    services_health = fields.Char(string='Health Service')
    services_psychosocial = fields.Char(string='Psychosocial Service')
    services_education = fields.Char(string='Education Service')
    services_legal = fields.Char(string='Legal Service')
    services_tracing = fields.Char(string='Family Tracing')
    services_other = fields.Char(string='Other Services')

    # ── 11 · follow-up record ────────────────────────────────────────────
    followup_line_ids = fields.One2many(
        'cp.partner.followup', 'record_id', string='Follow-up Record')

    # ── 12 · case closure, as the partner reported ───────────────────────
    case_status = fields.Selection([
        ('open', 'Open'),
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ], string='Reported Status', required=True, default='open',
        tracking=True)
    last_followup_date = fields.Date(string='Last Follow-up')
    closure_date = fields.Date(string='Date Closed')
    closure_reason = fields.Text(string='Reason for Closure')
    closure_summary = fields.Text(string='Closure Summary')
    closure_situation = fields.Text(string="Child's Situation at Closure")
    closure_feedback = fields.Text(string='Family Feedback')
    closure_approved_date = fields.Date(string='Approved On')

    case_id = fields.Many2one(
        'cp.case', string='MOWDAFA Case', readonly=True, copy=False,
        help='Set when MOWDAFA opens its own case from this record — '
             'the child has come into the ministry\'s care.')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    attachment_count = fields.Integer(
        compute='_compute_attachment_count', string='Documents')

    def _compute_attachment_count(self):
        counts = {}
        if self.ids:
            for res_id, count in self.env['ir.attachment']._read_group(
                    [('res_model', '=', 'cp.partner.record'),
                     ('res_id', 'in', self.ids)],
                    groupby=['res_id'], aggregates=['__count']):
                counts[res_id] = count
        for record in self:
            record.attachment_count = counts.get(record.id, 0)

    def action_view_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', 'cp.partner.record'),
                       ('res_id', '=', self.id)],
            'context': {'default_res_model': 'cp.partner.record',
                        'default_res_id': self.id},
        }

    # ── opening a MOWDAFA case from a deposited record ───────────────────
    def _case_values(self):
        """The reporting spine both tracks share, carried across so the
        officer does not key the child twice."""
        self.ensure_one()
        source = dict(self._fields['referral_source'].selection or [])
        return {
            'child_name': self.child_name,
            'sex': self.sex,
            'date_of_birth': self.date_of_birth,
            'dob_estimated': self.dob_estimated,
            'age_years': self.age_years,
            'nationality': self.nationality,
            'population_group': self.population_group,
            'disability': self.disability,
            'region_id': self.region_id.id,
            'district_id': self.district_id.id,
            'date_identified': self.date_identified,
            'referral_source': source.get(self.referral_source) or '',
            'protection_concern': self.protection_concern,
            'concern_description': self.concern_description,
            'risk_level': self.risk_level,
            'immediate_risk': self.immediate_risk,
            'risk_factors': self.risk_factors,
            'case_worker_id': self.partner_worker_id.id,
            'supervisor_id': self.partner_supervisor_id.id,
        }

    def action_create_case(self):
        """The child has come into MOWDAFA's care: open a managed case
        from what the partner already recorded. The deposited record is
        kept as it was — it is still the partner's submission."""
        self.ensure_one()
        if self.case_id:
            return self.action_open_case()
        case = self.env['cp.case'].create(self._case_values())
        self.case_id = case.id
        case.message_post(body=_(
            'Opened from partner record %s (%s).',
            self.name, self.partner_agency_id.display_name or ''))
        self.message_post(body=_(
            'MOWDAFA case %s opened from this record.', case.name))
        return self.action_open_case()

    def action_open_case(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('MOWDAFA Case'),
            'res_model': 'cp.case',
            'view_mode': 'form',
            'res_id': self.case_id.id,
            'target': 'current',
        }

    @api.depends('child_name', 'name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = '%s — %s' % (
                record.name, record.child_name or _('Not yet named'))

    @api.onchange('partner_agency_id')
    def _onchange_partner_agency_id(self):
        """Selecting the agency brings its known contacts onto the record.
        Anything already typed is left alone — the record wins."""
        for record in self:
            agency = record.partner_agency_id
            if not agency:
                continue
            if not record.partner_worker_id and agency.focal_point_id:
                record.partner_worker_id = agency.focal_point_id
            if not record.partner_supervisor_id and agency.supervisor_id:
                record.partner_supervisor_id = agency.supervisor_id

    def _learn_agency_contacts(self):
        """...and the reverse: a name the agency does not have yet is
        written back onto it, so the next record starts filled in."""
        for record in self:
            agency = record.partner_agency_id
            if not agency:
                continue
            values = {}
            if record.partner_worker_id and not agency.focal_point_id:
                values['focal_point_id'] = record.partner_worker_id.id
            if record.partner_supervisor_id and not agency.supervisor_id:
                values['supervisor_id'] = record.partner_supervisor_id.id
            if values:
                agency.sudo().write(values)

    @api.onchange('date_of_birth')
    def _onchange_date_of_birth(self):
        for record in self:
            if record.date_of_birth:
                today = fields.Date.context_today(record)
                record.age_years = max(
                    today.year - record.date_of_birth.year - (
                        (today.month, today.day) <
                        (record.date_of_birth.month, record.date_of_birth.day)),
                    0)

    @api.onchange('region_id')
    def _onchange_region_id(self):
        for record in self:
            if record.district_id and record.district_id.region_id != record.region_id:
                record.district_id = False

    # ── the partner report — its own dashboard, its own numbers ─────────
    @api.model
    def get_partner_report_data(self):
        """Everything the partner report shows, in one call. Scoped to
        this model alone, so 'records we hold' can never blur into
        'cases we handle'."""
        Record = self

        def count_by(field, domain=None):
            result = {}
            for key, count in Record._read_group(
                    domain or [], groupby=[field], aggregates=['__count']):
                result[key] = count
            return result

        total = Record.search_count([])
        active = Record.search_count(
            [('case_status', 'in', ('open', 'active'))])
        closed = Record.search_count([('case_status', '=', 'closed')])
        critical = Record.search_count(
            [('risk_level', 'in', ('critical', 'high'))])

        # by agency, with the status and risk split
        rows = {}
        for agency, status, count in Record._read_group(
                [], groupby=['partner_agency_id', 'case_status'],
                aggregates=['__count']):
            key = agency.id if agency else 0
            row = rows.setdefault(key, {
                'name': (agency.short_name or agency.name) if agency
                        else _('Unspecified'),
                'children': 0, 'active': 0, 'closed': 0, 'critical': 0,
            })
            row['children'] += count
            if status in ('open', 'active'):
                row['active'] += count
            elif status == 'closed':
                row['closed'] += count
        for agency, count in Record._read_group(
                [('risk_level', 'in', ('critical', 'high'))],
                groupby=['partner_agency_id'], aggregates=['__count']):
            key = agency.id if agency else 0
            if key in rows:
                rows[key]['critical'] = count
        agencies = sorted(rows.values(),
                          key=lambda r: r['children'], reverse=True)

        def named(field, labels=None):
            out = []
            for key, count in Record._read_group(
                    [], groupby=[field], aggregates=['__count']):
                if hasattr(key, 'name'):
                    label = key.name if key else _('Undefined')
                else:
                    label = (labels or {}).get(key, key or _('Undefined'))
                out.append({'name': label, 'count': count})
            out.sort(key=lambda r: r['count'], reverse=True)
            return out

        sex = count_by('sex')
        status = count_by('case_status')
        bands = [(0, 4, '0–4'), (5, 9, '5–9'), (10, 14, '10–14'),
                 (15, 17, '15–17')]
        ages = [{'name': label,
                 'count': Record.search_count(
                     [('age_years', '>=', lo), ('age_years', '<=', hi)])}
                for lo, hi, label in bands]
        over = Record.search_count([('age_years', '>', 17)])
        if over:
            ages.append({'name': '18+', 'count': over})

        today = fields.Date.context_today(self)
        return {
            'tiles': {
                'total': total,
                'active': active,
                'closed': closed,
                'critical': critical,
                'agency_count': len([a for a in agencies if a['children']]),
            },
            'period': '1 Jan – %s' % today.strftime('%d %b %Y'),
            'agencies': agencies,
            'regions': named('region_id'),
            'concerns': named('protection_concern', dict(CONCERNS)),
            'sex': [
                {'name': _('Female'), 'count': sex.get('female', 0)},
                {'name': _('Male'), 'count': sex.get('male', 0)},
            ],
            'ages': ages,
            'status': [
                {'name': _('Active'), 'count': (status.get('open', 0)
                                                + status.get('active', 0))},
                {'name': _('Pending'), 'count': status.get('pending', 0)},
                {'name': _('Closed'), 'count': status.get('closed', 0)},
                {'name': _('Critical/High'), 'count': critical},
            ],
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = vals.get('partner_case_id') or \
                    self.env['ir.sequence'].next_by_code(
                        'cp.partner.record') or 'New'
        records = super().create(vals_list)
        records._learn_agency_contacts()
        return records

    def write(self, vals):
        result = super().write(vals)
        if {'partner_agency_id', 'partner_worker_id',
                'partner_supervisor_id'} & set(vals):
            self._learn_agency_contacts()
        return result


class CpPartnerFollowup(models.Model):
    """Section 11 of the partner record: the follow-up rows the partner
    reported. Read as received — one line per visit."""
    _name = 'cp.partner.followup'
    _description = 'CP Partner Follow-up Line'
    _order = 'date desc, id desc'

    record_id = fields.Many2one(
        'cp.partner.record', string='Partner Record',
        required=True, ondelete='cascade')
    date = fields.Date(string='Date')
    progress = fields.Text(string='Progress')
    remaining_concerns = fields.Text(string='Remaining Concerns')
    next_actions = fields.Text(string='Next Actions')
