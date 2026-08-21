# -*- coding: utf-8 -*-
import math
from collections import defaultdict
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..models.gbv_case import AGE_BANDS, CHILD_BANDS, JUSTICE_ORDER
from .gbv_case_report_wizard import MONTH_ABBR, MONTH_SO

# Every printed string of the report, per wizard language. The template
# receives finished labels only, so it never branches on the language.
LABELS = {
    'so': {
        'confidential': 'XOG QARSOODI AH (CONFIDENTIAL)',
        'main_title': 'WARBIXINTA GUUD EE KIISASKA XADGUDUBKA',
        'period_word': 'Muddada',
        'pill_year': 'Sanadka', 'pill_region': 'Gobolka',
        'pill_type': 'Nooca', 'pill_source': 'Ilaha',
        'all_word': 'Dhammaan',
        'sec1': 'Tirakoobka Muhiimka ah',
        'kpi_total': 'WADARTA KIISASKA', 'kpi_total_sub': 'la diiwaangeliyay',
        'kpi_open': 'KIISAS FURAN', 'kpi_closed': 'LA XIDHAY',
        'kpi_court': 'MAXKAMAD', 'kpi_female': 'DUMAR',
        'kpi_male': 'RAG', 'kpi_children': 'CARUUR 0–17',
        'kpi_convicted': 'LA XUKUMAY',
        'of_total': 'wadarta', 'of_reported': 'la wariyay',
        'sec2': 'Kiisaska Gobol Kasta', 'sec2_sub': 'xaalad kasta',
        'th_region': 'Gobolka', 'th_open': 'Furan', 'th_closed': 'Xidhay',
        'th_court': 'Maxk.', 'th_total': 'Wadarta',
        'leg_open': 'Furan', 'leg_closed': 'La Xidhay',
        'leg_court': 'Maxkamad', 'total_row': 'WADARTA',
        'sec2_note': 'Gobollada aan wax xog ah soo gudbin lagama '
                     'muujin jaantuska.',
        'sec3': 'Xaaladda Kiisaska iyo Jinsiga Dhibbanayaasha',
        'sec3_left': 'Xaaladda Kiisaska',
        'sec3_right': 'Jinsiga Dhibbanayaasha',
        'kiis': 'KIIS', 'leg_female': 'Dumar', 'leg_male': 'Rag',
        'sec4': "Da'da Dhibbanayaasha",
        'sec4_sub': 'lagu xidhay taariikhda warbixinta',
        'grp_children': 'Caruur (0–17)',
        'grp_adults': 'Dadka waaweyn (18+)',
        'sec4_note': "%d kiis oo aan da'diisu diiwaangashanayn ayaa ku "
                     "jira wadarta laakiin lagama muujin qaybaha da'da.",
        'sec5': 'Nooca Xadgudubka',
        'sec6': 'Xiriirinta Adeegyada',
        'sec6_note': 'Dhibbane ayaa helay adeegyo badan — jaantusyadu '
                     'iskuma darsamaan wadarta kiisaska.',
        'title': 'WARBIXINTA GUUD EE DASHBOARD-KA',
        'subtitle_all_regions': 'Dhammaan 9 Gobol',
        'subtitle_all_types': 'Dhammaan noocyada xadgudubka',
        'tile_total': 'TIRADA GUUD', 'tile_open': 'KIISAS FURAN',
        'tile_closed': 'KIISAS XIRAN', 'tile_court': 'MAXKAMAD',
        'tile_convicted': 'LA XUKUMAY', 'tile_female': 'DUMAR',
        'tile_male': 'RAG', 'tile_children': 'CARRUUR',
        'unit_case': 'Kiis', 'unit_person': 'Qof',
        'prev_year': 'Sanadkii hore', 'change': 'Isbeddel',
        'region_title': 'KIISASKA GOBOLLADA',
        'region': 'Gobol', 'total': 'Wadar', 'open': 'Furan',
        'closed': 'Xiran', 'court': 'Maxkamad',
        'no_data': 'Wax xog ah kama aanu helin',
        'undefined': 'Aan la cayimin',
        'types_title': 'NOOCYADA XADGUDUBKA',
        'type': 'Nooca', 'share': 'Boqolkiiba',
        'ages_title': "DA'DA DHIBANAYAASHA",
        'age_band': "Da'da", 'child_note': 'Ka yar 18 sano',
        'services_title': 'ADEEGYADA LA BIXIYAY',
        'service': 'Adeegga',
        'months_title': 'ISBEDDELKA BILAHA',
        'month': 'Bisha',
        'funnel_title': 'MARXALADAHA CADDAALADDA',
        'stage': 'Marxaladda', 'reached': 'Gaaray',
        'funnel_stages': {
            'reported': 'La wariyay', 'investigated': 'La baaray',
            'arrested': 'La qabtay', 'in_court': 'Maxkamad',
            'convicted': 'La xukumay',
        },
        'sec7': 'Kiisaska Bishii',
        'sec7_note': 'Bisha %s ayaa ugu badan kiisaska la '
                     'diiwaangeliyay muddada.',
        'month_abbr': ['Jan', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                       'Lul', 'Ogo', 'Seb', 'Okt', 'Nof', 'Dis'],
        'sec8': 'Gaadhitaanka Cadaalad',
        'sec8_sub': 'saf-ka caddaaladda',
        'th_stage': 'Marxaladda', 'th_kiis': 'Kiis', 'th_pct': '%',
        'sec8_note': '%s kiisaska la wariyay ayaa ku dhammaaday xukun.',
        'sec9': 'Barbar Dhig — %s iyo %s',
        'th_no': 'NO', 'th_change': 'Isbedel',
        'org_line1': 'Waaxda Ka Hortagga Tacaddiyada ee Wasaaradda',
        'org_line2': 'Horumarinta Haweenka iyo Arrimaha Qoyska Puntland.',
        'org_email': 'gbv.department@mowdafa.pl.so',
    },
    'en': {
        'confidential': 'CONFIDENTIAL',
        'main_title': 'GBV CASES SUMMARY REPORT',
        'period_word': 'Period',
        'pill_year': 'Year', 'pill_region': 'Region',
        'pill_type': 'Type', 'pill_source': 'Source',
        'all_word': 'All',
        'sec1': 'Key Statistics',
        'kpi_total': 'TOTAL CASES', 'kpi_total_sub': 'registered',
        'kpi_open': 'OPEN CASES', 'kpi_closed': 'CLOSED',
        'kpi_court': 'IN COURT', 'kpi_female': 'FEMALE',
        'kpi_male': 'MALE', 'kpi_children': 'CHILDREN 0–17',
        'kpi_convicted': 'CONVICTED',
        'of_total': 'of total', 'of_reported': 'of reported',
        'sec2': 'Cases by Region', 'sec2_sub': 'by status',
        'th_region': 'Region', 'th_open': 'Open', 'th_closed': 'Closed',
        'th_court': 'Court', 'th_total': 'Total',
        'leg_open': 'Open', 'leg_closed': 'Closed',
        'leg_court': 'In court', 'total_row': 'TOTAL',
        'sec2_note': 'Regions that did not submit any data are not '
                     'shown in the chart.',
        'sec3': 'Case Status and Survivor Gender',
        'sec3_left': 'Case Status',
        'sec3_right': 'Survivor Gender',
        'kiis': 'CASES', 'leg_female': 'Female', 'leg_male': 'Male',
        'sec4': 'Survivor Age Bands',
        'sec4_sub': 'frozen at the report date',
        'grp_children': 'Children (0–17)',
        'grp_adults': 'Adults (18+)',
        'sec4_note': '%d case(s) without a recorded age are included in '
                     'the total but not shown in the age bands.',
        'sec5': 'Violence Type',
        'sec6': 'Service Linkage',
        'sec6_note': 'A survivor can receive several services — the bars '
                     'do not sum to the case total.',
        'title': 'DASHBOARD SUMMARY REPORT',
        'subtitle_all_regions': 'All 9 regions',
        'subtitle_all_types': 'All violence types',
        'tile_total': 'TOTAL CASES', 'tile_open': 'OPEN CASES',
        'tile_closed': 'CLOSED CASES', 'tile_court': 'IN COURT',
        'tile_convicted': 'CONVICTED', 'tile_female': 'FEMALE',
        'tile_male': 'MALE', 'tile_children': 'CHILDREN',
        'unit_case': 'Cases', 'unit_person': 'People',
        'prev_year': 'Previous year', 'change': 'Change',
        'region_title': 'CASES BY REGION',
        'region': 'Region', 'total': 'Total', 'open': 'Open',
        'closed': 'Closed', 'court': 'In court',
        'no_data': 'No data received',
        'undefined': 'Undefined',
        'types_title': 'VIOLENCE TYPES',
        'type': 'Type', 'share': 'Share',
        'ages_title': 'SURVIVOR AGE BANDS',
        'age_band': 'Age band', 'child_note': 'Under 18',
        'services_title': 'SERVICES PROVIDED',
        'service': 'Service',
        'months_title': 'MONTHLY TREND',
        'month': 'Month',
        'funnel_title': 'JUSTICE PIPELINE',
        'stage': 'Stage', 'reached': 'Reached',
        'funnel_stages': {
            'reported': 'Reported', 'investigated': 'Investigated',
            'arrested': 'Arrested', 'in_court': 'In court',
            'convicted': 'Convicted',
        },
        'sec7': 'Cases per Month',
        'sec7_note': 'The month of %s had the most registered cases '
                     'in the period.',
        'month_abbr': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'sec8': 'Justice Reach',
        'sec8_sub': 'the justice pipeline',
        'th_stage': 'Stage', 'th_kiis': 'Cases', 'th_pct': '%',
        'sec8_note': '%s of reported cases ended in conviction.',
        'sec9': 'Comparison — %s vs %s',
        'th_no': 'NO', 'th_change': 'Change',
        'org_line1': 'Department for the Prevention of Violence,',
        'org_line2': 'Ministry of Women Development and Family Affairs, '
                     'Puntland.',
        'org_email': 'gbv.department@mowdafa.pl.so',
    },
}

TILE_COLOURS = ['#e6f0e9', '#e8e8f2', '#dbeffa', '#fdf2d1',
                '#f9dce1', '#ececec', '#e6f0e9', '#dbeffa']

# Section 1 KPI cards, in print order: (label key, value colour, icon
# glyph, icon tint). Glyphs are ones DejaVu Sans actually has, so
# wkhtmltopdf prints them.
KPI_CARDS = [
    ('kpi_total', '#1F3A57', '▤', '#e8eef4'),
    ('kpi_open', '#2E75B6', '►', '#e6f0fa'),
    ('kpi_closed', '#1E7F46', '✓', '#e6f4ec'),
    ('kpi_court', '#C77D18', '▦', '#faf0e0'),
    ('kpi_female', '#157F76', '♀', '#e4f2f0'),
    ('kpi_male', '#8B959C', '♂', '#eef0f2'),
    ('kpi_children', '#C77D18', '⌂', '#faf0e0'),
    ('kpi_convicted', '#8B959C', '§', '#eef0f2'),
]


class GbvDashboardReportWizard(models.TransientModel):
    _name = 'gbv.dashboard.report.wizard'
    _description = 'GBV Dashboard Summary Report'

    # ------------------------------------------------------------------
    # Muddada (interval)
    # ------------------------------------------------------------------
    period = fields.Selection([
        ('this_year', 'This year'),
        ('last_year', 'Last year'),
        ('this_month', 'This month'),
        ('last_month', 'Last month'),
        ('this_quarter', 'This quarter'),
        ('q1', 'Q1 (Jan – Mar)'),
        ('q2', 'Q2 (Apr – Jun)'),
        ('q3', 'Q3 (Jul – Sep)'),
        ('q4', 'Q4 (Oct – Dec)'),
        ('custom', 'Custom interval'),
    ], string='Interval', default='this_year', required=True,
        help='A shortcut that fills the two dates. Touch either date and '
             'the interval switches to Custom.')
    year = fields.Integer(
        string='Year', required=True,
        default=lambda self: fields.Date.context_today(self).year,
        help='The year the quarter presets apply to.')
    date_from = fields.Date(
        string='From', required=True,
        default=lambda self: date(fields.Date.context_today(self).year, 1, 1))
    date_to = fields.Date(
        string='To', required=True,
        default=lambda self: date(fields.Date.context_today(self).year, 12, 31))

    # ------------------------------------------------------------------
    # Baaxadda (scope)
    # ------------------------------------------------------------------
    region_ids = fields.Many2many(
        'gbv.region', 'gbv_dash_wizard_region_rel',
        'wizard_id', 'region_id',
        string='Regions',
        help='Empty means all nine regions.')
    violence_type_ids = fields.Many2many(
        'gbv.violence.type', 'gbv_dash_wizard_type_rel',
        'wizard_id', 'type_id',
        string='Violence Type',
        help='Empty means every violence type together.')

    # ------------------------------------------------------------------
    # Qaabka daabacaadda (presentation)
    # ------------------------------------------------------------------
    lang = fields.Selection([
        ('so', 'Af-Soomaali'),
        ('en', 'English'),
    ], string='Language', default='so', required=True,
        help='The language every heading and label of the PDF prints in.')
    compare_previous = fields.Boolean(
        string='Compare with previous year', default=True,
        help='Adds last year\'s figures and the change per region.')
    include_charts = fields.Boolean(
        string='Include charts', default=True,
        help='Prints the bar charts under the tables. Untick for a '
             'tables-only report.')

    # ------------------------------------------------------------------
    # Wax-soo-saarka (output)
    # ------------------------------------------------------------------
    title_override = fields.Char(
        string='Custom title',
        help='Leave empty to build the title from the interval, e.g. '
             'WARBIXINTA GUUD EE DASHBOARD-KA 2026.')
    no_data_region_ids = fields.Many2many(
        'gbv.region', 'gbv_dash_wizard_nodata_rel',
        'wizard_id', 'region_id',
        string='Regions with no returns',
        help='Regions that submitted nothing at all for this period. They '
             'print "Wax xog ah kama aanu helin" across the row instead of '
             'zeros — a zero and a missing return are not the same fact.')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    # ------------------------------------------------------------------
    # Presets / constraints — same behaviour as the statistical report
    # ------------------------------------------------------------------
    @api.onchange('period', 'year')
    def _onchange_period(self):
        preset = self.env['gbv.case.report.wizard']._preset_dates(
            self.period, self.year)
        if preset:
            self.date_from, self.date_to = preset

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        for wizard in self:
            preset = self.env['gbv.case.report.wizard']._preset_dates(
                wizard.period, wizard.year)
            if preset and (wizard.date_from, wizard.date_to) != preset:
                wizard.period = 'custom'

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise UserError(_('The "From" date is after the "To" date.'))

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            'mowdafa_extended.action_report_gbv_dashboard'
        ).report_action(self, data={'wizard_id': self.id})

    # ==================================================================
    # Aggregation
    # ==================================================================
    def _labels(self):
        self.ensure_one()
        return LABELS[self.lang]

    def _case_domain(self, date_from, date_to):
        self.ensure_one()
        domain = [('date_reported', '>=', date_from),
                  ('date_reported', '<=', date_to)]
        if self.region_ids:
            domain.append(('region_id', 'in', self.region_ids.ids))
        if self.violence_type_ids:
            domain.append(('violence_type_id', 'in',
                           self.violence_type_ids.ids))
        return domain

    def _regions(self):
        self.ensure_one()
        if self.region_ids:
            return self.region_ids.sorted(lambda r: (r.sequence, r.id))
        return self.env['gbv.region'].search([])

    def _region_name(self, region):
        return region.somali_name or region.name \
            if self.lang == 'so' else region.name

    def _period_label(self):
        self.ensure_one()
        start, end = self.date_from, self.date_to
        full_year = (start.month, start.day) == (1, 1) \
            and (end.month, end.day) == (12, 31)
        if full_year and start.year == end.year:
            return str(start.year)
        if full_year:
            return '%s – %s' % (start.year, end.year)
        return '%s – %s' % (start.strftime('%d/%m/%Y'),
                            end.strftime('%d/%m/%Y'))

    @api.model
    def _build_donut(self, parts):
        """SVG donut geometry from [(label, value, colour), ...]: one
        thick-stroked arc path per part, so the template does no
        arithmetic. Paths, not stroke-dashoffset — wkhtmltopdf's WebKit
        mis-renders negative dash offsets. Zero parts stay in the legend
        but draw nothing; a lone part becomes a full circle (an arc
        whose ends coincide collapses to nothing)."""
        total = sum(value for _label, value, _colour in parts)
        segments, angle = [], -90.0
        for _label, value, colour in parts:
            if not value:
                continue
            sweep = 360.0 * value / total
            start, end = angle, angle + sweep
            angle = end
            if sweep >= 359.9:
                segments.append({'colour': colour, 'circle': True, 'd': ''})
                continue
            segments.append({
                'colour': colour,
                'circle': False,
                'd': 'M %.2f %.2f A 60 60 0 %d 1 %.2f %.2f' % (
                    80 + 60 * math.cos(math.radians(start)),
                    80 + 60 * math.sin(math.radians(start)),
                    1 if sweep > 180 else 0,
                    80 + 60 * math.cos(math.radians(end)),
                    80 + 60 * math.sin(math.radians(end)),
                ),
            })
        return {
            'empty': not segments,
            'segments': segments,
            'legend': [{'label': label, 'value': value, 'colour': colour}
                       for label, value, colour in parts],
        }

    @api.model
    def _change_label(self, current, previous):
        if not previous:
            return '–'
        return '%+.1f%%' % (100.0 * (current - previous) / previous)

    def _build_report_data(self):
        """Everything the PDF prints, labels included, in one dict. The
        template does no arithmetic and no translation."""
        self.ensure_one()
        labels = self._labels()
        Case = self.env['gbv.case']
        ChartWizard = self.env['gbv.case.report.wizard']
        domain = self._case_domain(self.date_from, self.date_to)
        prev_domain = self._case_domain(
            self.date_from - relativedelta(years=1),
            self.date_to - relativedelta(years=1))
        no_data_ids = set(self.no_data_region_ids.ids)
        cases = Case.search(domain)
        cases = cases.filtered(
            lambda c: c.region_id.id not in no_data_ids)
        prev_cases = Case.search(prev_domain)

        # ---- title -----------------------------------------------------
        title = self.title_override or '%s %s' % (
            labels['title'], self._period_label())
        if self.region_ids:
            scope_regions = ', '.join(
                self._region_name(region) for region in self._regions())
        else:
            scope_regions = labels['subtitle_all_regions']
        if self.violence_type_ids:
            scope_types = ', '.join(self.violence_type_ids.mapped(
                'somali_name' if self.lang == 'so' else 'name'))
        else:
            scope_types = labels['subtitle_all_types']
        subtitle = '%s · %s · %s – %s' % (
            scope_regions, scope_types,
            self.date_from.strftime('%d/%m/%Y'),
            self.date_to.strftime('%d/%m/%Y'))

        # ---- confidential header + filter pills ------------------------
        if self.lang == 'so':
            def fmt_date(value):
                return '%02d %s %d' % (
                    value.day, MONTH_SO[value.month - 1], value.year)
        else:
            def fmt_date(value):
                return value.strftime('%d %b %Y')
        if self.date_from.year == self.date_to.year:
            years_pill = str(self.date_from.year)
        else:
            years_pill = '%d – %d' % (self.date_from.year, self.date_to.year)
        header = {
            'confidential': labels['confidential'],
            'title': self.title_override or labels['main_title'],
            'period': '%s: %s — %s' % (
                labels['period_word'],
                fmt_date(self.date_from), fmt_date(self.date_to)),
            'pills': [
                (labels['pill_year'], years_pill),
                (labels['pill_region'], scope_regions),
                (labels['pill_type'],
                 scope_types if self.violence_type_ids
                 else labels['all_word']),
                (labels['pill_source'], 'gbv.case'),
            ],
        }

        # ---- tiles -----------------------------------------------------
        def count(extra):
            return len(cases.filtered(extra))

        total = len(cases)
        prev_total = len(prev_cases)
        tiles = [
            {'label': labels['tile_total'], 'value': total,
             'unit': labels['unit_case'],
             'delta': self._change_label(total, prev_total)
             if self.compare_previous and prev_total else ''},
            {'label': labels['tile_open'],
             'value': count(lambda c: c.case_status == 'open'),
             'unit': labels['unit_case'], 'delta': ''},
            {'label': labels['tile_closed'],
             'value': count(lambda c: c.case_status == 'closed'),
             'unit': labels['unit_case'], 'delta': ''},
            {'label': labels['tile_court'],
             'value': count(lambda c: c.justice_stage == 'in_court'),
             'unit': labels['unit_case'], 'delta': ''},
            {'label': labels['tile_convicted'],
             'value': count(lambda c: c.justice_stage == 'convicted'),
             'unit': labels['unit_case'], 'delta': ''},
            {'label': labels['tile_female'],
             'value': count(lambda c: c.sex == 'female'),
             'unit': labels['unit_person'], 'delta': ''},
            {'label': labels['tile_male'],
             'value': count(lambda c: c.sex == 'male'),
             'unit': labels['unit_person'], 'delta': ''},
            {'label': labels['tile_children'],
             'value': count(lambda c: c.is_child),
             'unit': labels['unit_person'], 'delta': ''},
        ]
        for index, tile in enumerate(tiles):
            tile['colour'] = TILE_COLOURS[index % len(TILE_COLOURS)]

        # ---- section 1: KPI cards -------------------------------------
        def pct(value, base=None):
            base = total if base is None else base
            return '%.1f%%' % (100.0 * value / base) if base else '0.0%'

        open_count = count(lambda c: c.case_status == 'open')
        closed_count = count(lambda c: c.case_status == 'closed')
        court_count = count(lambda c: c.justice_stage == 'in_court')
        convicted_count = count(lambda c: c.justice_stage == 'convicted')
        female_count = count(lambda c: c.sex == 'female')
        male_count = count(lambda c: c.sex == 'male')
        child_count = count(lambda c: c.is_child)
        kpi_values = {
            'kpi_total': (total, labels['kpi_total_sub']),
            'kpi_open': (open_count,
                         '%s %s' % (pct(open_count), labels['of_total'])),
            'kpi_closed': (closed_count,
                           '%s %s' % (pct(closed_count), labels['of_total'])),
            'kpi_court': (court_count,
                          '%s %s' % (pct(court_count), labels['of_total'])),
            'kpi_female': (female_count, pct(female_count)),
            'kpi_male': (male_count, pct(male_count)),
            'kpi_children': (child_count,
                             '%s %s' % (pct(child_count), labels['of_total'])),
            'kpi_convicted': (convicted_count,
                              '%s %s' % (pct(convicted_count),
                                         labels['of_reported'])),
        }
        kpis = []
        for key, colour, icon, tint in KPI_CARDS:
            value, sub = kpi_values[key]
            kpis.append({
                'label': labels[key], 'value': value, 'sub': sub,
                'colour': colour, 'icon': icon, 'icon_bg': tint,
                # The design colours the subline like the value; the total
                # card's subline is blue while its number stays navy.
                'sub_colour': '#2E75B6' if key == 'kpi_total' else colour,
            })

        # ---- section 3: status + gender donuts ------------------------
        sec3 = {
            'left': dict(
                self._build_donut([
                    (labels['leg_open'], open_count, '#2E75B6'),
                    (labels['leg_closed'], closed_count, '#1F4E79'),
                    (labels['leg_court'], court_count, '#C77D18'),
                ]),
                title=labels['sec3_left'], total=total,
                unit=labels['kiis']),
            'right': dict(
                self._build_donut([
                    (labels['leg_female'], female_count, '#157F76'),
                    (labels['leg_male'], male_count, '#A6AEB2'),
                ]),
                title=labels['sec3_right'], total=total,
                unit=labels['kiis']),
        }

        # ---- cases by region ------------------------------------------
        by_region = defaultdict(lambda: defaultdict(int))
        for case in cases:
            row = by_region[case.region_id.id]
            row['total'] += 1
            if case.case_status in ('open', 'closed'):
                row[case.case_status] += 1
            if case.justice_stage == 'in_court':
                row['court'] += 1
        prev_by_region = defaultdict(int)
        for case in prev_cases:
            prev_by_region[case.region_id.id] += 1

        region_rows = []
        for index, region in enumerate(self._regions(), start=1):
            missing = region.id in no_data_ids
            row = by_region[region.id]
            previous = prev_by_region[region.id]
            region_rows.append({
                'seq': index,
                'name': self._region_name(region),
                'no_data': missing,
                'total': 0 if missing else row['total'],
                'open': row['open'], 'closed': row['closed'],
                'court': row['court'],
                'prev': previous,
                'change': '–' if missing
                else self._change_label(row['total'], previous),
            })
        region_totals = {
            key: sum(row[key] for row in region_rows)
            for key in ('total', 'open', 'closed', 'court', 'prev')}
        region_totals['change'] = self._change_label(
            region_totals['total'], region_totals['prev'])

        # ---- section 2: cases per region, by status -------------------
        # Only regions that actually submitted something; the footnote
        # explains the missing ones. Sorted by total, like the dashboard.
        sec2_rows = sorted(
            [row for row in region_rows
             if not row['no_data'] and row['total']],
            key=lambda row: -row['total'])
        sec2_max = max([row['total'] for row in sec2_rows] or [1])
        sec2_bars = [{
            'name': row['name'],
            'total': row['total'],
            'open_w': '%.1f%%' % (100.0 * row['open'] / sec2_max),
            'closed_w': '%.1f%%' % (100.0 * row['closed'] / sec2_max),
            'court_w': '%.1f%%' % (100.0 * row['court'] / sec2_max),
        } for row in sec2_rows]
        sec2 = {
            'bars': sec2_bars,
            'rows': sec2_rows,
            'totals': {key: sum(row[key] for row in sec2_rows)
                       for key in ('open', 'closed', 'court', 'total')},
        }

        # ---- violence types -------------------------------------------
        type_counts = defaultdict(int)
        for case in cases:
            type_counts[case.violence_type_id] += 1
        type_rows = []
        for vtype, value in sorted(type_counts.items(),
                                   key=lambda item: -item[1]):
            if self.lang == 'so':
                name = vtype and (vtype.somali_name or vtype.name)
            else:
                name = vtype and vtype.name
            type_rows.append({
                'name': name or labels['undefined'],
                'count': value,
                'share': '%.1f%%' % (100.0 * value / total) if total else '–',
            })

        # ---- age bands -------------------------------------------------
        band_counts = defaultdict(int)
        for case in cases:
            band_counts[case.age_band] += 1
        age_rows = [{
            'name': label,
            'count': band_counts.get(label, 0),
            'is_child': label in CHILD_BANDS,
        } for lo, hi, label in AGE_BANDS]

        # ---- section 4: age-band bar chart ----------------------------
        adult_count = total - child_count
        unknown_age = total - sum(row['count'] for row in age_rows)
        left, right, top, bottom = 34.0, 706.0, 34.0, 168.0
        plot_height = bottom - top
        axis_max = max([row['count'] for row in age_rows] + [1])
        if axis_max <= 6:
            tick_values = list(range(axis_max + 1))
        else:
            axis_max, step = self.env[
                'gbv.case.report.wizard']._axis_scale(axis_max)
            tick_values = list(range(0, axis_max + 1, step))
        slot = (right - left) / len(age_rows)
        bar_width = min(46.0, slot * 0.55)
        child_slots = sum(1 for row in age_rows if row['is_child'])
        sec4_bars = []
        for index, row in enumerate(age_rows):
            centre = left + slot * index + slot / 2.0
            height = plot_height * row['count'] / axis_max
            sec4_bars.append({
                'label': row['name'],
                'value': row['count'],
                'colour': '#C77D18' if row['is_child'] else '#2E75B6',
                'x': round(centre - bar_width / 2.0, 1),
                'centre': round(centre, 1),
                'y': round(bottom - height, 1),
                'height': round(height, 1),
            })
        divider_x = round(left + slot * child_slots, 1)
        sec4 = {
            'bars': sec4_bars,
            'ticks': [{'label': value,
                       'y': round(bottom - plot_height * value / axis_max, 1)}
                      for value in tick_values],
            'left': left, 'right': right, 'top': top, 'bottom': bottom,
            'label_y': round(bottom + 14, 1),
            'divider_x': divider_x,
            'children_label': '%s %d · %s' % (
                labels['grp_children'], child_count, pct(child_count)),
            'adults_label': '%s %d · %s' % (
                labels['grp_adults'], adult_count, pct(adult_count)),
            'children_legend': '%s · %d · %s' % (
                labels['grp_children'], child_count, pct(child_count)),
            'adults_legend': '%s · %d · %s' % (
                labels['grp_adults'], adult_count, pct(adult_count)),
            'note': labels['sec4_note'] % unknown_age
            if unknown_age > 0 else '',
        }

        # ---- section 5: violence types as horizontal bars -------------
        sec5_max = max([row['count'] for row in type_rows] + [1])
        sec5 = {'bars': [{
            'name': row['name'],
            'count': row['count'],
            'share': row['share'],
            'width': '%.1f%%' % (100.0 * row['count'] / sec5_max),
        } for row in type_rows]}

        # ---- services --------------------------------------------------
        service_counts = defaultdict(int)
        for line in self.env['gbv.case.service'].search(
                [('case_id', 'in', cases.ids)]):
            service_counts[line.service_id.name] += 1
        service_rows = [{'name': name, 'count': value}
                        for name, value in sorted(service_counts.items(),
                                                  key=lambda item: -item[1])]

        # ---- section 6: service linkage bars --------------------------
        sec6_max = max([row['count'] for row in service_rows] + [1])
        sec6 = {
            'bars': [{
                'name': row['name'],
                'count': row['count'],
                'share': pct(row['count']),
                'width': '%.1f%%' % (100.0 * row['count'] / sec6_max),
            } for row in service_rows],
            'note': labels['sec6_note'],
        }

        # ---- monthly trend --------------------------------------------
        month_counts = defaultdict(int)
        for case in cases:
            month_counts[case.date_reported.month] += 1
        month_names = MONTH_SO if self.lang == 'so' else MONTH_ABBR
        month_rows = [{'name': month_names[month - 1],
                       'count': month_counts.get(month, 0)}
                      for month in range(1, 13)]

        # ---- section 7: monthly line chart ----------------------------
        month_values = [row['count'] for row in month_rows]
        axis_max7, step7 = self.env['gbv.case.report.wizard']._axis_scale(
            max(month_values + [1]))
        m_left, m_right, m_top, m_bottom = 34.0, 706.0, 20.0, 150.0
        m_plot = m_bottom - m_top
        points = []
        for index, row in enumerate(month_rows):
            points.append({
                'x': round(m_left + (m_right - m_left) * index / 11.0, 1),
                'y': round(m_bottom - m_plot * row['count'] / axis_max7, 1),
                'value': row['count'],
                'label': labels['month_abbr'][index],
            })
        polyline = ' '.join('%s,%s' % (p['x'], p['y']) for p in points)
        area = 'M %s %s L %s Z' % (
            points[0]['x'], m_bottom,
            ' L '.join('%s %s' % (p['x'], p['y']) for p in points)
            + (' L %s %s' % (points[-1]['x'], m_bottom)))
        peak_index = max(range(12), key=lambda i: month_values[i])
        sec7 = {
            'points': points,
            'polyline': polyline,
            'area': area,
            'ticks': [{'label': value,
                       'y': round(m_bottom - m_plot * value / axis_max7, 1)}
                      for value in range(0, axis_max7 + 1, step7)],
            'left': m_left, 'right': m_right,
            'top': m_top, 'bottom': m_bottom,
            'label_y': round(m_bottom + 16, 1),
            'note': labels['sec7_note'] % (
                MONTH_SO[peak_index] if self.lang == 'so'
                else date(2000, peak_index + 1, 1).strftime('%B'))
            if total else '',
        }

        # ---- justice funnel -------------------------------------------
        stage_counts = defaultdict(int)
        for case in cases:
            stage_counts[case.justice_stage] += 1
        funnel_rows = []
        for index, stage in enumerate(JUSTICE_ORDER):
            reached = sum(stage_counts.get(s, 0)
                          for s in JUSTICE_ORDER[index:])
            funnel_rows.append({
                'name': labels['funnel_stages'][stage],
                'count': reached,
                'pct': '%.1f%%' % (100.0 * reached / total) if total else '–',
            })

        # ---- section 8: justice funnel bars + table -------------------
        funnel_colours = ['#1F3A57', '#27577F', '#33689B',
                          '#9FBCD6', '#C2D4E4']
        funnel_max = max([row['count'] for row in funnel_rows] + [1])
        sec8 = {
            'bars': [{
                'name': row['name'],
                'count': row['count'],
                'pct': row['pct'],
                'stub': not row['count'],
                'width': '%.1f%%' % (100.0 * row['count'] / funnel_max),
                'colour': funnel_colours[index % len(funnel_colours)],
            } for index, row in enumerate(funnel_rows)],
            'rows': funnel_rows,
            'note': labels['sec8_note'] % pct(convicted_count)
            if total else '',
        }

        # ---- section 9: previous-year comparison ----------------------
        sec9 = False
        if self.compare_previous:
            label_current = self._period_label()
            previous_from = self.date_from - relativedelta(years=1)
            previous_to = self.date_to - relativedelta(years=1)
            full_year = (previous_from.month, previous_from.day) == (1, 1) \
                and (previous_to.month, previous_to.day) == (12, 31)
            if full_year and previous_from.year == previous_to.year:
                label_previous = str(previous_from.year)
            else:
                label_previous = '%s – %s' % (
                    previous_from.strftime('%d/%m/%Y'),
                    previous_to.strftime('%d/%m/%Y'))
            sec9_rows = sorted(
                [row for row in region_rows
                 if not row['no_data'] and (row['total'] or row['prev'])],
                key=lambda row: -row['total'])
            sec9 = {
                'title': labels['sec9'] % (label_previous, label_current),
                'label_previous': label_previous,
                'label_current': label_current,
                'rows': [dict(row, seq=index) for index, row
                         in enumerate(sec9_rows, start=1)],
                'totals': {
                    'prev': sum(row['prev'] for row in sec9_rows),
                    'total': sum(row['total'] for row in sec9_rows),
                    'change': self._change_label(
                        sum(row['total'] for row in sec9_rows),
                        sum(row['prev'] for row in sec9_rows)),
                },
            }

        # ---- charts ----------------------------------------------------
        charts = {}
        if self.include_charts:
            charts['regions'] = ChartWizard._build_bar_chart([
                {'label': row['name'], 'value': row['total'],
                 'no_data': row['no_data']} for row in region_rows])
            charts['months'] = ChartWizard._build_bar_chart([
                {'label': row['name'][:3], 'value': row['count'],
                 'no_data': False} for row in month_rows])
            charts['types'] = ChartWizard._build_bar_chart([
                {'label': row['name'], 'value': row['count'],
                 'no_data': False} for row in type_rows[:8]],
                bar_cap=34.0) if type_rows else False

        return {
            'labels': labels,
            'header': header,
            'kpis': kpis,
            'sec2': sec2,
            'sec3': sec3,
            'sec4': sec4,
            'sec5': sec5,
            'sec6': sec6,
            'sec7': sec7,
            'sec8': sec8,
            'sec9': sec9,
            'title': title,
            'subtitle': subtitle,
            'compare': self.compare_previous,
            'tiles': tiles,
            'region_rows': region_rows,
            'region_totals': region_totals,
            'type_rows': type_rows,
            'age_rows': age_rows,
            'service_rows': service_rows,
            'month_rows': month_rows,
            'funnel_rows': funnel_rows,
            'charts': charts,
        }
