# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

CP_STAGES = [
    ('handover', 'Hand-over'),
    ('registration', 'Registration'),
    ('verification', 'Verification'),
    ('in_care', 'In Care'),
    ('reunification', 'Reunification'),
    ('followup', 'Follow-up'),
]

RECOMMENDATIONS = [
    ('reunification', 'Reunification'),
    ('reunification_support', 'Reunification + Enhanced Support'),
    ('alt_care', 'Long-term Alternative Care'),
    ('tracing', 'Further Tracing'),
]

CONCERNS = [
    ('separated', 'Separated child'),
    ('unaccompanied', 'Unaccompanied'),
    ('street', 'On the street'),
    ('labour', 'Child labour'),
    ('trafficked', 'Trafficked'),
    ('orphan', 'Orphan'),
    ('disabled', 'Disabled'),
    ('abuse', 'Physical abuse'),
    ('neglect', 'Neglect'),
    ('risk_separation', 'Risk of separation'),
    ('other', 'Other'),
]


class CpCase(models.Model):
    """A child MOWDAFA cares for directly (CP-16 managed track).

    Live case: CP/YYYY/NNNN reference, six stages, verification
    recommendation, restricted photo. Partner-deposited records are a
    separate model, cp.partner.record — they never live here.
    """
    _name = 'cp.case'
    _description = 'Child Protection Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Case Reference', readonly=True, copy=False, default='New')

    # ── reporting spine (shared with cp.partner.record) ──────────────────
    child_name = fields.Char(string='Full Name', tracking=True)
    sex = fields.Selection(
        [('female', 'Female'), ('male', 'Male')], string='Sex', tracking=True)
    date_of_birth = fields.Date(string='Date of Birth')
    dob_estimated = fields.Boolean(string='DOB Estimated?')
    age_years = fields.Integer(string='Age (years)', tracking=True)
    nationality = fields.Char(string='Nationality', default='Somali')
    population_group = fields.Selection([
        ('resident', 'Resident'),
        ('host', 'Host Community'),
        ('idp', 'IDP'),
        ('refugee', 'Refugee'),
        ('returnee', 'Returnee'),
        ('other', 'Other'),
    ], string='Population Group', tracking=True)
    disability = fields.Boolean(string='Disability')
    region_id = fields.Many2one(
        'gbv.region', string='Region', tracking=True)
    district_id = fields.Many2one(
        'gbv.district', string='District', tracking=True,
        domain="[('region_id', '=?', region_id)]")
    date_identified = fields.Date(string='Date Identified')
    referral_source = fields.Char(string='Referral Source')
    protection_concern = fields.Selection(
        CONCERNS, string='Primary Concern', tracking=True)
    concern_description = fields.Text(string='Concern Description')
    risk_level = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('moderate', 'Moderate'),
        ('low', 'Low'),
    ], string='Risk Level', tracking=True)
    immediate_risk = fields.Boolean(string='Immediate Risk?')
    risk_factors = fields.Text(string='Risk Factors')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    # ── managed-only fields ──────────────────────────────────────────────
    photo = fields.Binary(
        string='Photograph', attachment=True, copy=False,
        groups='base.group_user',
        help='Restricted to the assigned worker and supervisor; never on '
             'a report unless explicitly a tracing document.')
    stage = fields.Selection(
        CP_STAGES, string='Stage', default='handover', tracking=True,
        group_expand='_group_expand_stage')
    recommendation = fields.Selection(
        RECOMMENDATIONS, string='Recommendation', tracking=True,
        help='The verification fork: drives reunification, alternative '
             'care or further tracing.')
    case_worker_id = fields.Many2one(
        'case.worker', string='Case Worker', tracking=True)
    supervisor_id = fields.Many2one(
        'case.worker', string='Supervisor', tracking=True)
    placement_type = fields.Selection([
        ('facility', 'Facility'),
        ('kinship', 'Kinship'),
        ('interim', 'Interim'),
        ('home', 'Home'),
    ], string='Placement', tracking=True)

    # ── the nine forms + placements (managed track) ─────────────────────
    placement_ids = fields.One2many(
        'cp.placement', 'case_id', string='Placements')
    handover_ids = fields.One2many(
        'cp.handover', 'case_id', string='Hand-overs')
    registration_ids = fields.One2many(
        'cp.registration', 'case_id', string='Registrations')
    verification_ids = fields.One2many(
        'cp.verification', 'case_id', string='Verifications')
    psychosocial_ids = fields.One2many(
        'cp.psychosocial', 'case_id', string='Psychosocial Sessions')
    reunification_ids = fields.One2many(
        'cp.reunification', 'case_id', string='Reunifications')
    cp_followup_ids = fields.One2many(
        'cp.followup', 'case_id', string='Follow-up Visits')

    # ── the verification gate ────────────────────────────────────────────
    verification_conflict = fields.Boolean(
        string='Accounts Disagree', compute='_compute_verification',
        store=True,
        help='The adult and child verifications recommend different '
             'things. The file stops here until a protection supervisor '
             'decides — a hard gate, not a warning.')
    supervisor_decision = fields.Selection(
        RECOMMENDATIONS, string='Supervisor Decision', tracking=True,
        help='Set by the protection supervisor to open the gate when '
             'the two accounts disagree.')
    supervisor_reason = fields.Text(
        string='Supervisor Reason',
        help='Required to open the gate. Both original records are '
             'kept untouched — the disagreement is evidence.')

    @api.depends('verification_ids.kind', 'verification_ids.recommendation')
    def _compute_verification(self):
        for case in self:
            adult = case.verification_ids.filtered(
                lambda v: v.kind == 'adult')[:1]
            child = case.verification_ids.filtered(
                lambda v: v.kind == 'child')[:1]
            case.verification_conflict = bool(
                adult and child
                and adult.recommendation != child.recommendation)

    def _sync_verification(self):
        """Where the two accounts agree, the case moves on its own."""
        for case in self:
            adult = case.verification_ids.filtered(
                lambda v: v.kind == 'adult')[:1]
            child = case.verification_ids.filtered(
                lambda v: v.kind == 'child')[:1]
            if adult and child and adult.recommendation == child.recommendation:
                case.recommendation = child.recommendation
                case._advance_stage('in_care')
            elif case.supervisor_decision:
                case.recommendation = case.supervisor_decision
                case._advance_stage('in_care')

    @api.constrains('supervisor_decision', 'supervisor_reason')
    def _check_supervisor_reason(self):
        for case in self:
            if case.supervisor_decision and not case.supervisor_reason:
                raise UserError(_(
                    'The gate will not open without a written reason. '
                    'The disagreement is evidence, not an error to be '
                    'tidied away.'))

    # ── stage machine ────────────────────────────────────────────────────
    CP_STAGE_ORDER = ['handover', 'registration', 'verification',
                      'in_care', 'reunification', 'followup']

    def _advance_stage(self, stage):
        """Move cases forward to `stage`; never backwards."""
        order = self.CP_STAGE_ORDER
        for case in self:
            if order.index(stage) > order.index(case.stage):
                case.stage = stage

    # ── smart-button counts ──────────────────────────────────────────────
    handover_count = fields.Integer(compute='_compute_form_counts')
    registration_count = fields.Integer(compute='_compute_form_counts')
    verification_count = fields.Integer(compute='_compute_form_counts')
    placement_count = fields.Integer(compute='_compute_form_counts')
    psychosocial_count = fields.Integer(compute='_compute_form_counts')
    reunification_count = fields.Integer(compute='_compute_form_counts')
    followup_visit_count = fields.Integer(compute='_compute_form_counts')
    adult_verified = fields.Boolean(compute='_compute_form_counts')
    child_verified = fields.Boolean(compute='_compute_form_counts')

    @api.depends('handover_ids', 'registration_ids', 'verification_ids',
                 'placement_ids', 'psychosocial_ids', 'reunification_ids',
                 'cp_followup_ids', 'verification_ids.kind')
    def _compute_form_counts(self):
        for case in self:
            case.handover_count = len(case.handover_ids)
            case.registration_count = len(case.registration_ids)
            case.verification_count = len(case.verification_ids)
            case.placement_count = len(case.placement_ids)
            case.psychosocial_count = len(case.psychosocial_ids)
            case.reunification_count = len(case.reunification_ids)
            case.followup_visit_count = len(case.cp_followup_ids)
            kinds = case.verification_ids.mapped('kind')
            case.adult_verified = 'adult' in kinds
            case.child_verified = 'child' in kinds

    # ── header buttons: open the next form pre-linked to this case ──────
    def _open_cp_form(self, model, name, extra_context=None):
        self.ensure_one()
        context = {'default_case_id': self.id}
        context.update(extra_context or {})
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': 'form',
            'target': 'current',
            'context': context,
        }

    def action_create_handover(self):
        return self._open_cp_form('cp.handover', _('Hand-over'))

    def action_create_registration(self):
        return self._open_cp_form('cp.registration', _('Registration'))

    def action_create_verification_adult(self):
        return self._open_cp_form(
            'cp.verification', _('Adult Verification'),
            {'default_kind': 'adult'})

    def action_create_verification_child(self):
        return self._open_cp_form(
            'cp.verification', _('Child Verification'),
            {'default_kind': 'child'})

    def action_create_reunification(self):
        return self._open_cp_form('cp.reunification', _('Reunification'))

    def action_create_followup_visit(self):
        return self._open_cp_form(
            'cp.followup', _('Follow-up Visit'),
            {'default_visit_number': self.followup_visit_count + 1})

    # ── smart buttons: open the case's records ──────────────────────────
    def _view_cp_records(self, model, name, records):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': 'tree,form',
            'domain': [('case_id', '=', self.id)],
            'context': {'default_case_id': self.id},
        }
        if len(records) == 1:
            action.update({'view_mode': 'form', 'res_id': records.id})
        return action

    def action_view_handovers(self):
        return self._view_cp_records(
            'cp.handover', _('Hand-overs'), self.handover_ids)

    def action_view_registrations(self):
        return self._view_cp_records(
            'cp.registration', _('Registrations'), self.registration_ids)

    def action_view_verifications(self):
        return self._view_cp_records(
            'cp.verification', _('Verifications'), self.verification_ids)

    def action_view_placements(self):
        return self._view_cp_records(
            'cp.placement', _('Placements'), self.placement_ids)

    def action_view_psychosocial(self):
        return self._view_cp_records(
            'cp.psychosocial', _('Psychosocial Sessions'),
            self.psychosocial_ids)

    def action_view_reunifications(self):
        return self._view_cp_records(
            'cp.reunification', _('Reunifications'), self.reunification_ids)

    def action_view_followup_visits(self):
        return self._view_cp_records(
            'cp.followup', _('Follow-up Visits'), self.cp_followup_ids)

    attachment_count = fields.Integer(
        compute='_compute_attachment_count', string='Documents')

    def _compute_attachment_count(self):
        counts = {}
        if self.ids:
            for res_id, count in self.env['ir.attachment']._read_group(
                    [('res_model', '=', 'cp.case'), ('res_id', 'in', self.ids)],
                    groupby=['res_id'], aggregates=['__count']):
                counts[res_id] = count
        for case in self:
            case.attachment_count = counts.get(case.id, 0)

    def action_view_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', 'cp.case'),
                       ('res_id', '=', self.id)],
            'context': {'default_res_model': 'cp.case',
                        'default_res_id': self.id},
        }

    @api.model
    def _group_expand_stage(self, stages, domain, order=None):
        return [key for key, _label in CP_STAGES]

    @api.depends('child_name', 'name')
    def _compute_display_name(self):
        for case in self:
            if case.child_name:
                case.display_name = '%s — %s' % (case.name, case.child_name)
            else:
                case.display_name = '%s — %s' % (
                    case.name, _('Not yet named'))

    @api.onchange('date_of_birth')
    def _onchange_date_of_birth(self):
        for case in self:
            if case.date_of_birth:
                today = fields.Date.context_today(case)
                case.age_years = max(
                    today.year - case.date_of_birth.year - (
                        (today.month, today.day) <
                        (case.date_of_birth.month, case.date_of_birth.day)),
                    0)

    @api.onchange('region_id')
    def _onchange_region_id(self):
        for case in self:
            if case.district_id and case.district_id.region_id != case.region_id:
                case.district_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'cp.case') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if 'supervisor_decision' in vals:
            self._sync_verification()
        return result

    # ── dashboard — one RPC, two source tables (managed / partner) ──────
    @api.model
    def get_dashboard_data(self):
        Case = self
        Partner = self.env['cp.partner.record']

        def count_by(model, field, domain):
            result = {}
            for key, count in model._read_group(
                    domain, groupby=[field], aggregates=['__count']):
                result[key] = count
            return result

        stage_counts = count_by(Case, 'stage', [])
        reco_counts = count_by(Case, 'recommendation', [])
        placement = count_by(Case, 'placement_type', [])

        partner_total = Partner.search_count([])
        partner_active = Partner.search_count(
            [('case_status', 'in', ('open', 'active'))])
        partner_closed = Partner.search_count([('case_status', '=', 'closed')])
        partner_critical = Partner.search_count(
            [('risk_level', 'in', ('critical', 'high'))])

        tiles = {
            'in_care': stage_counts.get('in_care', 0),
            'facility': placement.get('facility', 0),
            'kinship': (placement.get('kinship', 0)
                        + placement.get('interim', 0)
                        + placement.get('home', 0)),
            'verification': stage_counts.get('verification', 0),
            'reunified': (stage_counts.get('reunification', 0)
                          + stage_counts.get('followup', 0)),
            'managed_total': Case.search_count([]),
            'partner_total': partner_total,
            'partner_active': partner_active,
            'partner_closed': partner_closed,
            'partner_critical': partner_critical,
        }

        stages = [{'key': key, 'label': label,
                   'count': stage_counts.get(key, 0)}
                  for key, label in CP_STAGES]
        recommendations = [{'key': key, 'label': label,
                            'count': reco_counts.get(key, 0)}
                           for key, label in RECOMMENDATIONS]

        # partner report — by agency, with status and risk split
        agency_rows = {}
        for agency, status, count in Partner._read_group(
                [], groupby=['partner_agency_id', 'case_status'],
                aggregates=['__count']):
            key = agency.id if agency else 0
            row = agency_rows.setdefault(key, {
                'name': agency.name if agency else _('Unspecified'),
                'children': 0, 'active': 0, 'closed': 0, 'critical': 0,
            })
            row['children'] += count
            if status in ('open', 'active'):
                row['active'] += count
            elif status == 'closed':
                row['closed'] += count
        for agency, count in Partner._read_group(
                [('risk_level', 'in', ('critical', 'high'))],
                groupby=['partner_agency_id'], aggregates=['__count']):
            key = agency.id if agency else 0
            if key in agency_rows:
                agency_rows[key]['critical'] = count
        agencies = sorted(agency_rows.values(),
                          key=lambda r: r['children'], reverse=True)

        def named_counts(model, field, domain, labels=None):
            rows = []
            for key, count in model._read_group(
                    domain, groupby=[field], aggregates=['__count']):
                if hasattr(key, 'name'):
                    label = key.name if key else _('Undefined')
                else:
                    label = (labels or {}).get(key, key or _('Undefined'))
                rows.append({'name': label, 'count': count})
            rows.sort(key=lambda r: r['count'], reverse=True)
            return rows

        concern_labels = dict(CONCERNS)
        sex_counts = count_by(Partner, 'sex', [])
        tiles['agency_count'] = len([a for a in agencies if a['children']])

        # age bands, as the mockup prints them: 0–4, 5–9, 10–14, 15–17
        age_bands = [(0, 4, '0–4'), (5, 9, '5–9'),
                     (10, 14, '10–14'), (15, 17, '15–17')]
        partner_ages = [{
            'name': label,
            'count': Partner.search_count(
                [('age_years', '>=', lo), ('age_years', '<=', hi)]),
        } for lo, hi, label in age_bands]
        over_17 = Partner.search_count([('age_years', '>', 17)])
        if over_17:
            partner_ages.append({'name': '18+', 'count': over_17})

        status_counts = count_by(Partner, 'case_status', [])
        partner_status = [
            {'name': _('Active'), 'count': (status_counts.get('open', 0)
                                            + status_counts.get('active', 0))},
            {'name': _('Pending'), 'count': status_counts.get('pending', 0)},
            {'name': _('Closed'), 'count': status_counts.get('closed', 0)},
            {'name': _('Critical/High'), 'count': tiles['partner_critical']},
        ]

        return {
            'tiles': tiles,
            'stages': stages,
            'recommendations': recommendations,
            'partner_agencies': agencies,
            'partner_regions': named_counts(Partner, 'region_id', []),
            'partner_concerns': named_counts(
                Partner, 'protection_concern', [], concern_labels),
            'partner_sex': [
                {'name': _('Female'), 'count': sex_counts.get('female', 0)},
                {'name': _('Male'), 'count': sex_counts.get('male', 0)},
            ],
            'partner_ages': partner_ages,
            'partner_status': partner_status,
        }
