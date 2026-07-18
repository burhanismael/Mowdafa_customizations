# -*- coding: utf-8 -*-
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _

AGE_BANDS = [
    (0, 5, '0–5'), (6, 11, '6–11'), (12, 15, '12–15'), (16, 17, '16–17'),
    (18, 24, '18–24'), (25, 40, '25–40'), (41, 60, '41–60'), (61, 200, '60+'),
]
CHILD_BANDS = [label for lo, hi, label in AGE_BANDS if hi < 18]
JUSTICE_ORDER = ['reported', 'investigated', 'arrested', 'in_court', 'convicted']


class GbvService(models.Model):
    """Service sector master (health, psychosocial, legal, security,
    shelter, livelihood — the 6 sectors)."""
    _name = 'gbv.service'
    _description = 'GBV Service Sector'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    active = fields.Boolean(default=True)


class GbvCase(models.Model):
    """The case spine: one record per case, everything else hangs off it.
    Dashboard reads ONE table, so the figures can never disagree."""
    _name = 'gbv.case'
    _description = 'GBV Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Case Reference', readonly=True, copy=False, default='New')
    survivor_id = fields.Many2one(
        comodel_name='survivor.master', string='Survivor',
        required=True, tracking=True, index=True,
    )
    case_worker_id = fields.Many2one(
        comodel_name='case.worker', string='Case Worker', tracking=True)
    region_id = fields.Many2one(
        comodel_name='gbv.region', string='Region', required=True, tracking=True)
    district_id = fields.Many2one(
        comodel_name='gbv.district', string='District', tracking=True,
        domain="[('region_id', 'in', (region_id, False))]",
    )
    date_reported = fields.Date(
        string='Date Reported', required=True,
        default=fields.Date.context_today, tracking=True)
    date_incident = fields.Date(string='Date of Incident', tracking=True)
    entry_channel = fields.Selection(
        selection=[
            ('self', 'Self / Walk-in'),
            ('police', 'Police referral'),
            ('health', 'Health facility'),
            ('community', 'Community / CBO'),
            ('hotline', 'Hotline'),
            ('other', 'Other'),
        ],
        string='Entry Channel', tracking=True,
    )
    reported_by = fields.Char(string='Reported By')

    # ── classification — this is what the dashboard counts ──────────────
    violence_type_id = fields.Many2one(
        comodel_name='gbv.violence.type', string='Violence Type',
        required=True, tracking=True)
    risk_level_id = fields.Many2one(
        comodel_name='gbv.risk.level', string='Risk Level', tracking=True)
    population_group = fields.Selection(
        selection=[
            ('resident', 'Resident'),
            ('idp', 'IDP'),
            ('refugee', 'Refugee'),
            ('returnee', 'Returnee'),
            ('host', 'Host Community'),
        ],
        string='Population Group', tracking=True,
    )
    sex = fields.Selection(
        selection=[('female', 'Female'), ('male', 'Male')],
        string='Sex', required=True, tracking=True)
    # computed AND stored — frozen at report date, so a survivor who turns 18
    # next month doesn't silently move out of the children figure
    age_band = fields.Char(
        string='Age Band', compute='_compute_age_fields', store=True,
        readonly=False)
    is_child = fields.Boolean(
        string='Is a Child', compute='_compute_age_fields', store=True,
        readonly=False)

    # ── the two independent pipelines ────────────────────────────────────
    service_stage = fields.Selection(
        selection=[
            ('consent', 'Consent'),
            ('intake', 'Intake'),
            ('admission', 'Admission'),
            ('action_plan', 'Action Plan'),
            ('followup', 'Follow-up'),
            ('referral', 'Referral'),
            ('closure', 'Closure'),
        ],
        string='Service Stage', default='consent', tracking=True,
        group_expand='_group_expand_service_stage',
    )

    SERVICE_STAGE_ORDER = ['consent', 'intake', 'admission', 'action_plan',
                           'followup', 'referral', 'closure']

    def _advance_service_stage(self, stage):
        """Move cases forward to `stage`; never move a case backwards."""
        order = self.SERVICE_STAGE_ORDER
        for case in self:
            if order.index(stage) > order.index(case.service_stage):
                case.service_stage = stage
    justice_stage = fields.Selection(
        selection=[
            ('reported', 'Reported'),
            ('investigated', 'Investigated'),
            ('arrested', 'Arrested'),
            ('in_court', 'In Court'),
            ('convicted', 'Convicted'),
        ],
        string='Justice Stage', default='reported', tracking=True,
    )
    age_years = fields.Integer(
        string='Age (years)',
        compute='_compute_age_years', store=True, readonly=False,
        tracking=True,
        help='Exact age at the date reported, for the oldest/youngest '
             'tiles on the statistical report. Filled from the survivor '
             'birth date when there is one, typed otherwise. 0 prints '
             'as a dash.',
    )

    @api.onchange('region_id')
    def _onchange_region_id_district(self):
        for record in self:
            if record.district_id and record.district_id.region_id != record.region_id:
                record.district_id = False

    @api.onchange('district_id')
    def _onchange_district_id(self):
        for record in self:
            if record.district_id and not record.region_id:
                record.region_id = record.district_id.region_id

    @api.depends('survivor_id.birth_date', 'date_reported')
    def _compute_age_years(self):
        for record in self:
            born = record.survivor_id.birth_date
            on_date = record.date_reported or fields.Date.context_today(record)
            if born and on_date:
                years = on_date.year - born.year - (
                    (on_date.month, on_date.day) < (born.month, born.day))
                record.age_years = max(years, 0)
            elif not record.age_years:
                record.age_years = 0

    # justice pipeline details
    police_reference = fields.Char(string='Police Reference', tracking=True)
    investigating_officer = fields.Char(string='Investigating Officer')
    investigation_opened = fields.Date(string='Investigation Opened')
    arrest_date = fields.Date(string='Arrest Date')
    court = fields.Char(string='Court')
    court_file_no = fields.Char(string='Court File No.')
    first_hearing = fields.Date(string='First Hearing')
    verdict = fields.Char(string='Verdict')
    sentence = fields.Char(string='Sentence')

    case_status = fields.Selection(
        selection=[('open', 'Open'), ('closed', 'Closed')],
        string='Case Status', compute='_compute_case_status', store=True,
        help='Computed from the two pipelines; never typed.',
    )

    perpetrator_ids = fields.One2many(
        comodel_name='gbv.case.perpetrator', inverse_name='case_id',
        string='Perpetrators')
    service_ids = fields.One2many(
        comodel_name='gbv.case.service', inverse_name='case_id',
        string='Services & Referrals')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    # linked satellite forms (each satellite carries case_id)
    consent_ids = fields.One2many('survivor.case', 'case_id', string='Consent Forms')
    admission_ids = fields.One2many('admission.form', 'case_id', string='Admission Forms')
    action_plan_ids = fields.One2many('action.plan', 'case_id', string='Action Plans')
    followup_ids = fields.One2many('followup.form', 'case_id', string='Follow-ups')
    referral_ids = fields.One2many('referral.form', 'case_id', string='Referral Forms')
    closure_ids = fields.One2many('case.closure', 'case_id', string='Closures')
    consent_count = fields.Integer(compute='_compute_form_counts')
    admission_count = fields.Integer(compute='_compute_form_counts')
    action_plan_count = fields.Integer(compute='_compute_form_counts')
    followup_count = fields.Integer(compute='_compute_form_counts')
    referral_count = fields.Integer(compute='_compute_form_counts')
    closure_count = fields.Integer(compute='_compute_form_counts')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('gbv.case') or 'New'
        return super().create(vals_list)

    @api.model
    def _group_expand_service_stage(self, stages, domain, order=None):
        return [key for key, _label in self._fields['service_stage'].selection]

    @api.depends('survivor_id.birth_date', 'date_reported', 'survivor_id')
    def _compute_age_fields(self):
        for case in self:
            birth = case.survivor_id.birth_date
            report = case.date_reported or fields.Date.context_today(case)
            if not birth:
                case.age_band = False
                case.is_child = False
                continue
            age = relativedelta(report, birth).years
            case.is_child = age < 18
            case.age_band = next(
                (label for lo, hi, label in AGE_BANDS if lo <= age <= hi), '60+')

    @api.depends('service_stage')
    def _compute_case_status(self):
        for case in self:
            case.case_status = 'closed' if case.service_stage == 'closure' else 'open'

    def _compute_form_counts(self):
        for case in self:
            case.consent_count = len(case.consent_ids)
            case.admission_count = len(case.admission_ids)
            case.action_plan_count = len(case.action_plan_ids)
            case.followup_count = len(case.followup_ids)
            case.referral_count = len(case.referral_ids)
            case.closure_count = len(case.closure_ids)

    @api.onchange('survivor_id')
    def _onchange_survivor(self):
        if self.survivor_id and 'sex' in self.survivor_id._fields and self.survivor_id.sex:
            self.sex = 'female' if self.survivor_id.sex in ('female', 'f') else 'male'

    # ── header actions: open a satellite form pre-linked to this case ───
    def _open_satellite(self, model, name):
        self.ensure_one()
        context = {
            'default_case_id': self.id,
            'default_survivor_id': self.survivor_id.id,
        }
        if 'case_worker_id' in self.env[model]._fields and self.case_worker_id:
            context['default_case_worker_id'] = self.case_worker_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': 'form',
            'target': 'current',
            'context': context,
        }

    def action_create_consent(self):
        return self._open_satellite('survivor.case', 'Consent Form')

    consent_confirmed = fields.Boolean(
        compute='_compute_consent_confirmed',
        help='True once at least one consent form of this case is confirmed.')
    action_plan_confirmed = fields.Boolean(
        compute='_compute_action_plan_confirmed',
        help='True once at least one action plan of this case is confirmed.')

    @api.depends('consent_ids.state')
    def _compute_consent_confirmed(self):
        for case in self:
            case.consent_confirmed = any(
                consent.state == 'confirmed' for consent in case.consent_ids)

    @api.depends('action_plan_ids.state')
    def _compute_action_plan_confirmed(self):
        for case in self:
            case.action_plan_confirmed = any(
                plan.state == 'confirmed' for plan in case.action_plan_ids)

    closure_ready = fields.Boolean(
        compute='_compute_closure_ready',
        help='True once a follow-up or a referral of this case is confirmed.')

    @api.depends('followup_ids.state', 'referral_ids.state')
    def _compute_closure_ready(self):
        for case in self:
            case.closure_ready = any(
                f.state == 'confirmed' for f in case.followup_ids
            ) or any(
                r.state == 'confirmed' for r in case.referral_ids)

    def action_create_closure(self):
        return self._open_satellite('case.closure', 'Case Closure')

    def action_create_action_plan(self):
        return self._open_satellite('action.plan', 'Action Plan')

    def action_create_admission(self):
        action = self._open_satellite('admission.form', 'Admission Form')
        consent = self.consent_ids.filtered(
            lambda c: c.state == 'confirmed')[:1]
        if consent:
            action['context']['default_consent_form_id'] = consent.id
        return action

    def action_new_followup(self):
        return self._open_satellite('followup.form', 'New Follow-up')

    # ── smart buttons: open the case's linked records, or a new pre-linked
    # form when none exist yet ──
    def _view_satellite_records(self, model, name, records):
        self.ensure_one()
        context = {
            'default_case_id': self.id,
            'default_survivor_id': self.survivor_id.id,
        }
        if 'case_worker_id' in self.env[model]._fields and self.case_worker_id:
            context['default_case_worker_id'] = self.case_worker_id.id
        action = {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': 'tree,form',
            'domain': [('case_id', '=', self.id)],
            'context': context,
        }
        if not records:
            action.update({'view_mode': 'form', 'res_id': False})
        elif len(records) == 1:
            action.update({'view_mode': 'form', 'res_id': records.id})
        return action

    def action_view_consents(self):
        return self._view_satellite_records(
            'survivor.case', 'Consent Forms', self.consent_ids)

    def action_view_admissions(self):
        return self._view_satellite_records(
            'admission.form', 'Admission Forms', self.admission_ids)

    def action_view_action_plans(self):
        return self._view_satellite_records(
            'action.plan', 'Action Plans', self.action_plan_ids)

    def action_view_followups(self):
        return self._view_satellite_records(
            'followup.form', 'Follow-up Forms', self.followup_ids)

    def action_view_referrals(self):
        return self._view_satellite_records(
            'referral.form', 'Referral Forms', self.referral_ids)

    def action_view_closures(self):
        return self._view_satellite_records(
            'case.closure', 'Case Closures', self.closure_ids)


    # ------------------------------------------------------------------
    # Dashboard data — one RPC, one source table
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard_data(self, year=False, region_id=False):
        """Return every aggregate the dashboard needs in a single call."""
        Case = self.with_context(active_test=True)

        year_groups = Case._read_group(
            [], groupby=['date_reported:year'], aggregates=['__count'])
        years = sorted({g[0].year for g in year_groups if g[0]}, reverse=True)
        today_year = fields.Date.context_today(self).year
        if not years:
            years = [today_year]
        year = int(year) if year else years[0]

        def year_domain(y):
            domain = [('date_reported', '>=', date(y, 1, 1)),
                      ('date_reported', '<=', date(y, 12, 31))]
            if region_id:
                domain.append(('region_id', '=', int(region_id)))
            return domain

        domain = year_domain(year)
        prev_domain = year_domain(year - 1)

        def count_by(field, dom):
            result = {}
            for key, count in Case._read_group(
                    dom, groupby=[field], aggregates=['__count']):
                result[key] = count
            return result

        # --- Tiles -----------------------------------------------------
        total = Case.search_count(domain)
        prev_total = Case.search_count(prev_domain)
        status = count_by('case_status', domain)
        sex = count_by('sex', domain)
        totals = {
            'total': total,
            'prev_total': prev_total,
            'open': status.get('open', 0),
            'closed': status.get('closed', 0),
            'court': Case.search_count(
                domain + [('justice_stage', '=', 'in_court')]),
            'female': sex.get('female', 0),
            'male': sex.get('male', 0),
            'children': Case.search_count(
                domain + [('is_child', '=', True)]),
            'convicted': Case.search_count(
                domain + [('justice_stage', '=', 'convicted')]),
        }

        # --- Cases by region, with status split and delta --------------
        region_status = Case._read_group(
            domain, groupby=['region_id', 'case_status'],
            aggregates=['__count'])
        prev_by_region = count_by('region_id', prev_domain)
        region_map = {}
        for region, stat, count in region_status:
            key = region.id if region else 0
            row = region_map.setdefault(key, {
                'id': key,
                'name': region.name if region else _('Undefined'),
                'total': 0, 'prev': 0, 'open': 0, 'closed': 0, 'court': 0,
            })
            row['total'] += count
            if stat in row:
                row[stat] += count
        for region, count in prev_by_region.items():
            key = region.id if region else 0
            if key in region_map:
                region_map[key]['prev'] = count
        regions = sorted(region_map.values(),
                         key=lambda r: r['total'], reverse=True)

        # --- Age bands, in band order ----------------------------------
        age_counts = count_by('age_band', domain)
        ages = [{'key': label, 'label': label,
                 'count': age_counts.get(label, 0),
                 'is_child': label in CHILD_BANDS}
                for lo, hi, label in AGE_BANDS]

        # --- Violence types --------------------------------------------
        types = [{'name': vtype.name if vtype else _('Undefined'),
                  'count': count}
                 for vtype, count in Case._read_group(
                     domain, groupby=['violence_type_id'],
                     aggregates=['__count'])]
        types.sort(key=lambda t: t['count'], reverse=True)

        # --- Service lines (lines, not cases) --------------------------
        line_domain = [('case_id.date_reported', '>=', date(year, 1, 1)),
                       ('case_id.date_reported', '<=', date(year, 12, 31))]
        if region_id:
            line_domain.append(('case_id.region_id', '=', int(region_id)))
        services = [{'name': sector.name if sector else _('Undefined'),
                     'count': count}
                    for sector, count in self.env['gbv.case.service']._read_group(
                        line_domain, groupby=['service_id'],
                        aggregates=['__count'])]
        services.sort(key=lambda s: s['count'], reverse=True)

        # --- Monthly trend ---------------------------------------------
        month_counts = [0] * 12
        for month, count in Case._read_group(
                domain, groupby=['date_reported:month'],
                aggregates=['__count']):
            if month:
                month_counts[month.month - 1] = count
        months = [{'label': label, 'count': month_counts[index]}
                  for index, label in enumerate(
                      ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])]

        # --- Justice funnel (cumulative down the pipeline) -------------
        justice_counts = count_by('justice_stage', domain)
        labels = dict(self._fields['justice_stage'].selection)
        funnel = []
        for index, stage in enumerate(JUSTICE_ORDER):
            reached = sum(justice_counts.get(s, 0)
                          for s in JUSTICE_ORDER[index:])
            funnel.append({'key': stage, 'label': labels[stage],
                           'count': reached})

        return {
            'year': year,
            'region_id': int(region_id) if region_id else False,
            'filters': {
                'years': years,
                'regions': self.env['gbv.region'].search_read(
                    [], ['name'], order='name'),
            },
            'totals': totals,
            'regions': regions,
            'ages': ages,
            'types': types,
            'services': services,
            'months': months,
            'funnel': funnel,
        }


class GbvCasePerpetrator(models.Model):
    _name = 'gbv.case.perpetrator'
    _description = 'GBV Case Perpetrator'

    case_id = fields.Many2one(
        'gbv.case', string='Case', required=True, ondelete='cascade')
    name = fields.Char(string='Identifier / Initials')
    sex = fields.Selection(
        selection=[('female', 'Female'), ('male', 'Male'), ('unknown', 'Unknown')],
        string='Sex', default='unknown')
    age_estimate = fields.Integer(string='Age (est.)')
    relationship = fields.Selection(
        selection=[
            ('family', 'Family member'),
            ('partner', 'Intimate partner'),
            ('neighbour', 'Neighbour / Community'),
            ('authority', 'Person in authority'),
            ('stranger', 'Stranger'),
            ('unknown', 'Unknown'),
        ],
        string='Relationship to Survivor', default='unknown')
    status = fields.Selection(
        selection=[
            ('at_large', 'At large'),
            ('arrested', 'Arrested'),
            ('charged', 'Charged'),
            ('convicted', 'Convicted'),
        ],
        string='Status', default='at_large')
    charge = fields.Char(string='Charge')
    verdict = fields.Char(string='Verdict')
    age_years = fields.Integer(
        string='Age (years)',
        help='Exact age, for the oldest / youngest perpetrator tiles on '
             'the statistical report. 0 when unknown.',
    )
    notes = fields.Char(string='Notes')


class GbvCaseService(models.Model):
    _name = 'gbv.case.service'
    _description = 'GBV Case Service / Referral Line'

    case_id = fields.Many2one(
        'gbv.case', string='Case', required=True, ondelete='cascade')
    service_id = fields.Many2one(
        'gbv.service', string='Service Sector', required=True)
    state = fields.Selection(
        selection=[
            ('needed', 'Needed'),
            ('provided', 'Provided'),
            ('referred', 'Referred out'),
            ('declined', 'Declined'),
        ],
        string='Status', default='needed')
    date = fields.Date(string='Date')
    provider = fields.Char(string='Provider')
    notes = fields.Char(string='Notes')


# ── the spine link: each already-built form gains ONE field (case_id) ────
# required=False at schema level so existing records survive the upgrade;
# the case form always sets it via default_case_id.

class SurvivorCaseSpine(models.Model):
    _inherit = 'survivor.case'

    case_id = fields.Many2one(
        'gbv.case', string='Case', ondelete='cascade', index=True)


class AdmissionFormSpine(models.Model):
    _inherit = 'admission.form'

    case_id = fields.Many2one(
        'gbv.case', string='Case', ondelete='cascade', index=True)


class ActionPlanSpine(models.Model):
    _inherit = 'action.plan'

    case_id = fields.Many2one(
        'gbv.case', string='Case', ondelete='cascade', index=True)


class FollowupFormSpine(models.Model):
    _inherit = 'followup.form'

    case_id = fields.Many2one(
        'gbv.case', string='Case', ondelete='cascade', index=True)


class ReferralFormSpine(models.Model):
    _inherit = 'referral.form'

    case_id = fields.Many2one(
        'gbv.case', string='Case', ondelete='cascade', index=True)


class CaseClosureSpine(models.Model):
    _inherit = 'case.closure'

    case_id = fields.Many2one(
        'gbv.case', string='Case', ondelete='cascade', index=True)
