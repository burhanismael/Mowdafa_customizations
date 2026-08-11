# -*- coding: utf-8 -*-
import math
from collections import defaultdict
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

MONTH_ABBR = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

MONTH_SO = ['Janaayo', 'Febraayo', 'Maarso', 'Abriil', 'Maajo', 'Juun',
            'Luulyo', 'Ogosto', 'Sebtembar', 'Oktoobar', 'Nofembar',
            'Diseembar']

# Card colours for the district breakdown, cycled per region. Taken from
# the 2022 report, which uses a different header colour per region card.
CARD_COLOURS = ['#F2382F', '#E9508E', '#8A4C20', '#19A8D8',
                '#CCB821', '#BF6687', '#7F9C68', '#6A4C93', '#7C878D']

# Perpetrator statuses that count as "La Qabtay" (apprehended). Anything
# past arrest still means the man was caught, so the tile does not shrink
# when the case moves on to court.
CAUGHT_STATUSES = ('arrested', 'charged', 'convicted')

# Page two: bar colour, and the pie slice colour per victim sex.
BAR_COLOUR = '#E24A3B'
SEX_COLOURS = {'female': '#C00000', 'male': '#FFC000', 'other': '#7C878D'}

# Page three: last year against this one.
COMPARE_COLOURS = {'previous': '#EE4B3B', 'current': '#14181B'}


class GbvCaseReportWizard(models.TransientModel):
    _name = 'gbv.case.report.wizard'
    _description = 'GBV Cases Statistical Report'

    # ------------------------------------------------------------------
    # Interval
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
    date_from = fields.Date(string='From', required=True,
                            default=lambda self: self._default_date_from())
    date_to = fields.Date(string='To', required=True,
                          default=lambda self: self._default_date_to())

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    violence_type_ids = fields.Many2many(
        'gbv.violence.type', 'gbv_report_wizard_type_rel',
        'wizard_id', 'type_id',
        string='Violence Type',
        help='Empty prints every type together under one title. Pick one '
             'for a single report. Pick several and tick "One report per '
             'type" to get a complete report for each, one after another '
             'in the same PDF.')
    split_by_type = fields.Boolean(
        string='One report per type', default=False,
        help='Prints the full report once per selected violence type, each '
             'with its own title page, instead of one combined report.')
    region_ids = fields.Many2many(
        'gbv.region', 'gbv_report_wizard_region_rel',
        'wizard_id', 'region_id',
        string='Regions',
        help='Empty means all nine regions.')
    no_data_region_ids = fields.Many2many(
        'gbv.region', 'gbv_report_wizard_nodata_rel',
        'wizard_id', 'region_id',
        string='Regions with no returns',
        help='Regions that submitted nothing at all for this period. They '
             'print "Wax xog ah kama aanu helin" across the row instead of '
             'zeros — a zero and a missing return are not the same fact.')
    compare_previous = fields.Boolean(
        string='Compare with previous year', default=True,
        help='Adds the last page: the same interval one year earlier, per '
             'region, as a table and grouped bars.')
    title_override = fields.Char(
        string='Title override',
        help='Leave empty to build the title from the violence type and '
             'the interval, e.g. XOGTA KIISASKA KUFSIGA PUNTLAND 2026.')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    # ------------------------------------------------------------------
    # Defaults / onchange
    # ------------------------------------------------------------------
    @api.model
    def _default_date_from(self):
        return date(fields.Date.context_today(self).year, 1, 1)

    @api.model
    def _default_date_to(self):
        return date(fields.Date.context_today(self).year, 12, 31)

    @api.model
    def _preset_dates(self, period, year=None):
        """The two dates a preset stands for, or None for 'custom'."""
        today = fields.Date.context_today(self)
        year = year or today.year
        if period == 'this_year':
            return date(today.year, 1, 1), date(today.year, 12, 31)
        if period == 'last_year':
            return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)
        if period == 'this_month':
            start = today.replace(day=1)
            return start, start + relativedelta(months=1, days=-1)
        if period == 'last_month':
            start = today.replace(day=1) - relativedelta(months=1)
            return start, start + relativedelta(months=1, days=-1)
        if period == 'this_quarter':
            start = date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)
            return start, start + relativedelta(months=3, days=-1)
        if period in ('q1', 'q2', 'q3', 'q4'):
            start = date(year, {'q1': 1, 'q2': 4, 'q3': 7, 'q4': 10}[period], 1)
            return start, start + relativedelta(months=3, days=-1)
        return None

    @api.onchange('period', 'year')
    def _onchange_period(self):
        preset = self._preset_dates(self.period, self.year)
        if preset:
            self.date_from, self.date_to = preset

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        # Typing a date by hand means the preset no longer describes the
        # interval, so stop claiming it does.
        for wizard in self:
            preset = wizard._preset_dates(wizard.period, wizard.year)
            if preset and (wizard.date_from, wizard.date_to) != preset:
                wizard.period = 'custom'

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise UserError(_('The "From" date is after the "To" date.'))

    # ------------------------------------------------------------------
    # Print
    # ------------------------------------------------------------------
    def action_print(self):
        self.ensure_one()
        if self.split_by_type and not self.violence_type_ids:
            raise UserError(_(
                'Tick "One report per type" only after choosing which '
                'violence types to print. Leave the types empty and every '
                'type is reported together instead.'))
        return self.env.ref(
            'mowdafa_extended.action_report_gbv_cases'
        ).report_action(self, data={'wizard_id': self.id})

    # ==================================================================
    # Aggregation
    # ==================================================================
    def _columns(self):
        """Month columns while the interval is 14 months or less, year
        columns beyond that. A five-year request is a legitimate ask and
        60 month columns is not a page."""
        self.ensure_one()
        first = self.date_from.replace(day=1)
        last = self.date_to.replace(day=1)
        months, cursor = [], first
        while cursor <= last:
            months.append(cursor)
            cursor += relativedelta(months=1)
        multiyear = self.date_from.year != self.date_to.year
        if len(months) <= 14:
            return 'month', [{
                'key': (m.year, m.month),
                'label': MONTH_ABBR[m.month - 1],
                'sub': str(m.year)[-2:] if multiyear else '',
            } for m in months]
        years = sorted({m.year for m in months})
        return 'year', [{'key': y, 'label': str(y), 'sub': ''} for y in years]

    def _period_label(self):
        self.ensure_one()
        start, end = self.date_from, self.date_to
        full_year = (start.month, start.day) == (1, 1) and (end.month, end.day) == (12, 31)
        if full_year and start.year == end.year:
            return str(start.year)
        if full_year:
            return '%s – %s' % (start.year, end.year)
        same_month = (start.year, start.month) == (end.year, end.month)
        if same_month and start.day == 1 and (end + relativedelta(days=1)).month != end.month:
            return '%s %s' % (MONTH_SO[start.month - 1].upper(), start.year)
        return '%s – %s' % (start.strftime('%d/%m/%Y'), end.strftime('%d/%m/%Y'))

    def _type_word(self, vtypes):
        """The violence type as it reads inside a Somali title."""
        self.ensure_one()
        if len(vtypes) == 1:
            return (vtypes.somali_name or vtypes.name or '').upper()
        return 'XADGUDUBKA'

    def _block_title(self, vtypes):
        self.ensure_one()
        if self.title_override:
            return self.title_override
        return 'XOGTA KIISASKA %s PUNTLAND %s' % (
            self._type_word(vtypes), self._period_label())

    def _block_subtitle(self, vtypes):
        self.ensure_one()
        if len(vtypes) == 1:
            scope = vtypes.name
        elif vtypes:
            scope = ', '.join(vtypes.mapped('name'))
        else:
            scope = _('All violence types')
        return '%s · %s – %s' % (
            scope,
            self.date_from.strftime('%d %b %Y'),
            self.date_to.strftime('%d %b %Y'),
        )

    def _regions(self):
        self.ensure_one()
        if self.region_ids:
            return self.region_ids.sorted(lambda r: (r.sequence, r.id))
        return self.env['gbv.region'].search([])

    def _case_domain(self, vtypes, date_from, date_to):
        self.ensure_one()
        domain = [('date_reported', '>=', date_from),
                  ('date_reported', '<=', date_to)]
        if vtypes:
            domain.append(('violence_type_id', 'in', vtypes.ids))
        if self.region_ids:
            domain.append(('region_id', 'in', self.region_ids.ids))
        return domain

    def _build_blocks(self):
        """One block per printed report. Either a single combined block or
        one per violence type when the officer asked for them apart."""
        self.ensure_one()
        if self.split_by_type:
            return [self._build_block(vtype) for vtype in self.violence_type_ids]
        return [self._build_block(self.violence_type_ids)]

    def _build_block(self, vtypes):
        self.ensure_one()
        mode, columns = self._columns()
        regions = self._regions()
        cases = self.env['gbv.case'].search(
            self._case_domain(vtypes, self.date_from, self.date_to))

        def bucket(case):
            reported = case.date_reported
            return (reported.year, reported.month) if mode == 'month' else reported.year

        # ---- region x period matrix -----------------------------------
        matrix = defaultdict(int)
        for case in cases:
            matrix[(case.region_id.id, bucket(case))] += 1

        no_data_ids = set(self.no_data_region_ids.ids)
        rows, column_totals = [], {column['key']: 0 for column in columns}
        grand_total = 0
        for index, region in enumerate(regions, start=1):
            if region.id in no_data_ids:
                rows.append({
                    'seq': index,
                    'name': region.somali_name or region.name,
                    'no_data': True,
                    'cells': [],
                    'total': 0,
                })
                continue
            cells = []
            row_total = 0
            for column in columns:
                count = matrix.get((region.id, column['key']), 0)
                cells.append(count)
                column_totals[column['key']] += count
                row_total += count
            grand_total += row_total
            rows.append({
                'seq': index,
                'name': region.somali_name or region.name,
                'no_data': False,
                'cells': cells,
                'total': row_total,
            })

        # ---- district cards -------------------------------------------
        by_district = defaultdict(int)
        unspecified = defaultdict(int)
        for case in cases:
            if case.district_id:
                by_district[case.district_id.id] += 1
            elif case.region_id:
                unspecified[case.region_id.id] += 1
        districts = self.env['gbv.district'].search(
            [('region_id', 'in', regions.ids)])
        cards = []
        for index, region in enumerate(regions):
            if region.id in no_data_ids:
                continue
            region_districts = districts.filtered(lambda d: d.region_id == region)
            lines, total = [], 0
            for line_index, district in enumerate(region_districts, start=1):
                count = by_district.get(district.id, 0)
                total += count
                lines.append({
                    'seq': '%02d' % line_index,
                    'name': district.somali_label,
                    'count': count,
                })
            if unspecified.get(region.id):
                total += unspecified[region.id]
                lines.append({
                    'seq': '--',
                    'name': _('Aan la cayimin (district not recorded)'),
                    'count': unspecified[region.id],
                })
            cards.append({
                'region': region.somali_name or region.name,
                'colour': CARD_COLOURS[index % len(CARD_COLOURS)],
                'lines': lines,
                'total': total,
            })

        # Three cards to a row, padded, so the template does no arithmetic.
        card_rows = [cards[index:index + 3] + [None] * (3 - len(cards[index:index + 3]))
                     for index in range(0, len(cards), 3)]

        # ---- bar chart -------------------------------------------------
        bars = [{'label': row['name'],
                 'value': row['total'],
                 'no_data': row['no_data']} for row in rows]
        bar_max = max([bar['value'] for bar in bars] + [1])
        for bar in bars:
            bar['pct'] = round(100.0 * bar['value'] / bar_max, 1)

        # ---- victim sex ------------------------------------------------
        sex = {'female': 0, 'male': 0, 'other': 0}
        for case in cases:
            if case.sex == 'female':
                sex['female'] += 1
            elif case.sex == 'male':
                sex['male'] += 1
            else:
                sex['other'] += 1
        sex_total = sum(sex.values()) or 1
        sex['total'] = sum(sex.values())
        sex['female_pct'] = round(100.0 * sex['female'] / sex_total, 1)
        sex['male_pct'] = round(100.0 * sex['male'] / sex_total, 1)
        sex['other_pct'] = round(100.0 * sex['other'] / sex_total, 1)
        # Donut geometry: circumference of an r=60 circle, pre-computed so
        # the template stays free of arithmetic.
        circumference = 377.0
        sex['female_dash'] = '%.1f %.1f' % (
            circumference * sex['female_pct'] / 100.0, circumference)
        sex['male_dash'] = '%.1f %.1f' % (
            circumference * sex['male_pct'] / 100.0, circumference)
        sex['male_offset'] = '-%.1f' % (circumference * sex['female_pct'] / 100.0)
        sex['other_dash'] = '%.1f %.1f' % (
            circumference * sex['other_pct'] / 100.0, circumference)
        sex['other_offset'] = '-%.1f' % (
            circumference * (sex['female_pct'] + sex['male_pct']) / 100.0)
        sex['pie'] = self._build_pie([
            (_('Gabdho'), sex['female'], SEX_COLOURS['female']),
            (_('Wiilal'), sex['male'], SEX_COLOURS['male']),
            (_('Kale'), sex['other'], SEX_COLOURS['other']),
        ])

        # ---- victim age -------------------------------------------------
        ages = [case.age_years for case in cases if case.age_years]
        under_18 = len(cases.filtered('is_child'))
        banded = cases.filtered(lambda c: c.age_band)
        age = {
            'total': len(cases),
            'under_18': under_18,
            'over_18': len(banded) - len(banded.filtered('is_child')),
            'unknown': len(cases) - len(banded),
            'oldest': max(ages) if ages else 0,
            'youngest': min(ages) if ages else 0,
        }
        age['tiles'] = [
            {'label': 'TIRADA GUUD', 'value': age['total'],
             'unit': _('Dhibane'), 'colour': '#e6f0e9'},
            {'label': 'KA YAR 18 SANNO', 'value': age['under_18'],
             'unit': _('Dhibane'), 'colour': '#e8e8f2'},
            {'label': 'KA WEYN 18 SANNO', 'value': age['over_18'],
             'unit': _('Dhibane'), 'colour': '#dbeffa'},
            {'label': 'DHIBANAHA UGU WEYN', 'value': age['oldest'],
             'unit': _('Sano jir'), 'colour': '#fdf2d1'},
            {'label': 'DHIBANAHA UGU YAR', 'value': age['youngest'],
             'unit': _('Sano jir'), 'colour': '#f9dce1'},
        ]
        # The three counts side by side, wider bars than the region
        # chart because there are only three of them.
        age['columns'] = [
            {'label': _('Tirada Guud'), 'value': age['total']},
            {'label': _('Ka yar 18'), 'value': age['under_18']},
            {'label': _('Ka weyn 18'), 'value': age['over_18']},
        ]
        age['chart'] = self._build_bar_chart(
            [dict(column, no_data=False) for column in age['columns']],
            bar_cap=34.0)

        # ---- perpetrators ------------------------------------------------
        perpetrators = self.env['gbv.case.perpetrator'].search(
            [('case_id', 'in', cases.ids)])
        perp_ages = [p.age_years for p in perpetrators if p.age_years]
        perp = {
            'total': len(perpetrators),
            'caught': len(perpetrators.filtered(
                lambda p: p.status in CAUGHT_STATUSES)),
            'at_large': len(perpetrators.filtered(
                lambda p: p.status == 'at_large')),
            'oldest': max(perp_ages) if perp_ages else 0,
            'youngest': min(perp_ages) if perp_ages else 0,
        }
        perp_max = max([perp['total'], 1])
        perp['caught_pct'] = round(100.0 * perp['caught'] / perp_max, 1)
        perp['at_large_pct'] = round(100.0 * perp['at_large'] / perp_max, 1)
        perp['tiles'] = [
            {'label': 'TIRADA GUUD', 'value': perp['total'],
             'unit': _('Eedaysane'), 'colour': '#e6f0e9'},
            {'label': 'LA QABTAY', 'value': perp['caught'],
             'unit': _('Eedaysane'), 'colour': '#e8e8f2'},
            {'label': 'BAXSAD', 'value': perp['at_large'],
             'unit': _('Eedaysane'), 'colour': '#dbeffa'},
        ]
        perp['age_tiles'] = [
            {'label': 'EEDAYSANAHA UGU WEYN', 'value': perp['oldest'],
             'unit': _('Sano jir'), 'colour': '#ececec'},
            {'label': 'EEDAYSANAHA UGU YAR', 'value': perp['youngest'],
             'unit': _('Sano jir'), 'colour': '#f9dce1'},
        ]
        perp['columns'] = [
            {'label': _('Eedaysanayaasha'), 'value': perp['total']},
            {'label': _('La qabtay'), 'value': perp['caught']},
            {'label': _('Baxsad'), 'value': perp['at_large']},
        ]
        perp['chart'] = self._build_bar_chart(
            [dict(column, no_data=False) for column in perp['columns']],
            bar_cap=34.0)

        # ---- previous-year comparison -------------------------------------
        compare = self._build_comparison(vtypes, regions, no_data_ids) \
            if self.compare_previous else False
        if compare:
            compare['title'] = 'DHACDOOYINKA %s %s IYO %s' % (
                self._type_word(vtypes),
                compare['label_previous'], compare['label_current'])
            compare['grouped'] = self._build_grouped_chart(compare['rows'])

        return {
            'title': self._block_title(vtypes),
            'subtitle': self._block_subtitle(vtypes),
            'chart_title': 'JAANTUSKA KIISASKA %s EE GOBOLADA.'
                           % self._type_word(vtypes),
            'sex_title': 'TIRADA WIILASHA IYO HAWEENKA DHIBANAHA AH.',
            'age_title': "DA'DA DHIBANAYAASHA",
            'age_subtitle': 'Dhibanayaasha ka yar 18 iyo Toban iyo inta ka weyn',
            'age_legend': "Da'da Dhibanayaasha",
            'perp_title': 'XOGTA EEDAYSANAYAASHA FIL-DAMBIYEEDYADA %s'
                          % self._type_word(vtypes),
            'perp_subtitle': 'Tirada Guud, Inta la qabtay iyo Inta Baxsad ka ah',
            'perp_legend': 'Xogta Eedaysanayaasha',
            'mode': mode,
            'columns': columns,
            'rows': rows,
            'column_totals': [column_totals[column['key']] for column in columns],
            'grand_total': grand_total,
            'cards': cards,
            'card_rows': card_rows,
            'bars': bars,
            'chart': self._build_bar_chart(bars),
            'sex': sex,
            'age': age,
            'perp': perp,
            'compare': compare,
        }

    # ==================================================================
    # Page two — bar chart per region, pie chart per victim sex
    # ==================================================================
    @api.model
    def _axis_scale(self, max_value):
        """A round axis maximum with at most eight gridlines, so the
        labels stay readable at print size. The 15% headroom keeps the
        tallest bar off the top gridline."""
        for step in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
            axis_max = int(math.ceil(max(max_value * 1.15, 4) / float(step)) * step)
            if axis_max / step <= 8:
                return axis_max, step
        return axis_max, step

    @api.model
    def _build_bar_chart(self, bars, bar_cap=20.0):
        """SVG geometry for a bar chart, in user units. Bars flagged
        no_data get the "Xog kama helin" note where the bar would have
        been — a missing return is not a zero."""
        left, right, top, bottom = 34.0, 344.0, 14.0, 196.0
        values = [bar['value'] for bar in bars if not bar['no_data']]
        axis_max, step = self._axis_scale(max(values) if values else 0)
        plot_height = bottom - top

        ticks, value = [], 0
        while value <= axis_max:
            ticks.append({
                'label': value,
                'y': round(bottom - plot_height * value / axis_max, 1),
            })
            value += step

        slot = (right - left) / (len(bars) or 1)
        bar_width = min(bar_cap, slot * 0.5)
        items = []
        for index, bar in enumerate(bars):
            centre = left + slot * index + slot / 2.0
            height = 0.0 if bar['no_data'] else plot_height * bar['value'] / axis_max
            items.append({
                'label': bar['label'],
                'value': bar['value'],
                'no_data': bar['no_data'],
                'centre': round(centre, 1),
                'x': round(centre - bar_width / 2.0, 1),
                'width': round(bar_width, 1),
                'y': round(bottom - height, 1),
                'height': round(height, 1),
            })
        return {
            'width': 360, 'height': 250,
            'left': left, 'right': right, 'top': top, 'bottom': bottom,
            'label_y': round(bottom + 8, 1),
            'nodata_y': round(bottom - 34, 1),
            'colour': BAR_COLOUR,
            'ticks': ticks,
            'bars': items,
        }

    @api.model
    def _build_grouped_chart(self, rows):
        """Two bars per region, last year beside this one. Full page
        width, and the plot starts where the table below it does so the
        columns line up under their bars."""
        left, right, top, bottom = 62.0, 716.0, 14.0, 240.0
        values = [row['previous'] for row in rows]
        values += [0 if row['no_data'] else row['current'] for row in rows]
        axis_max, step = self._axis_scale(max(values) if values else 0)
        plot_height = bottom - top

        ticks, value = [], 0
        while value <= axis_max:
            ticks.append({
                'label': value,
                'y': round(bottom - plot_height * value / axis_max, 1),
            })
            value += step

        slot = (right - left) / (len(rows) or 1)
        bar_width = min(26.0, slot * 0.34)
        groups = []
        for index, row in enumerate(rows):
            centre = left + slot * index + slot / 2.0
            pair = []
            for offset, (value, colour) in enumerate((
                    (row['previous'], COMPARE_COLOURS['previous']),
                    (0 if row['no_data'] else row['current'],
                     COMPARE_COLOURS['current']))):
                height = plot_height * value / axis_max
                pair.append({
                    'x': round(centre - bar_width + bar_width * offset, 1),
                    'y': round(bottom - height, 1),
                    'width': round(bar_width, 1),
                    'height': round(height, 1),
                    'colour': colour,
                })
            groups.append({'label': row['name'], 'bars': pair})
        return {
            'width': 720, 'height': 246,
            'left': left, 'right': right, 'top': top, 'bottom': bottom,
            'ticks': ticks, 'groups': groups,
            'previous_colour': COMPARE_COLOURS['previous'],
            'current_colour': COMPARE_COLOURS['current'],
        }

    @api.model
    def _build_pie(self, parts):
        """SVG pie geometry from [(label, value, colour), ...]. A single
        non-zero part is drawn as a plain circle: an arc whose start and
        end coincide would collapse to nothing."""
        centre, radius = 100.0, 88.0
        drawn = [part for part in parts if part[1]]
        pie = {'centre': centre, 'radius': radius, 'total': sum(p[1] for p in parts),
               'circle': False, 'slices': []}
        if not drawn:
            return pie
        total = float(sum(part[1] for part in drawn))
        for label, value, colour in drawn:
            pie['slices'].append({
                'label': label, 'value': value, 'colour': colour,
                'pct': round(100.0 * value / total, 1), 'd': ''})
        if len(drawn) == 1:
            pie['circle'] = drawn[0][2]
            return pie
        angle = -90.0
        for slice_ in pie['slices']:
            sweep = 360.0 * slice_['value'] / total
            start, end = angle, angle + sweep
            angle = end
            slice_['d'] = 'M %.1f %.1f L %.1f %.1f A %.1f %.1f 0 %d 1 %.1f %.1f Z' % (
                centre, centre,
                centre + radius * math.cos(math.radians(start)),
                centre + radius * math.sin(math.radians(start)),
                radius, radius, 1 if sweep > 180 else 0,
                centre + radius * math.cos(math.radians(end)),
                centre + radius * math.sin(math.radians(end)),
            )
        return pie

    def _build_comparison(self, vtypes, regions, no_data_ids):
        self.ensure_one()
        previous_from = self.date_from - relativedelta(years=1)
        previous_to = self.date_to - relativedelta(years=1)
        current = self.env['gbv.case'].search_count(
            self._case_domain(vtypes, self.date_from, self.date_to))
        counts_current = defaultdict(int)
        counts_previous = defaultdict(int)
        for case in self.env['gbv.case'].search(
                self._case_domain(vtypes, self.date_from, self.date_to)):
            counts_current[case.region_id.id] += 1
        for case in self.env['gbv.case'].search(
                self._case_domain(vtypes, previous_from, previous_to)):
            counts_previous[case.region_id.id] += 1

        rows, total_current, total_previous = [], 0, 0
        for index, region in enumerate(regions, start=1):
            missing = region.id in no_data_ids
            value_current = 0 if missing else counts_current.get(region.id, 0)
            value_previous = counts_previous.get(region.id, 0)
            total_current += value_current
            total_previous += value_previous
            if value_previous:
                change = '%+.1f%%' % (
                    100.0 * (value_current - value_previous) / value_previous)
            else:
                change = '–'
            rows.append({
                'seq': index,
                'name': region.somali_name or region.name,
                'current': value_current,
                'previous': value_previous,
                'change': change,
                'no_data': missing,
            })
        scale = max([row['current'] for row in rows]
                    + [row['previous'] for row in rows] + [1])
        for row in rows:
            row['current_pct'] = round(100.0 * row['current'] / scale, 1)
            row['previous_pct'] = round(100.0 * row['previous'] / scale, 1)
        return {
            'label_current': self._period_label(),
            'label_previous': self._interval_label(previous_from, previous_to),
            'rows': rows,
            'total_current': total_current,
            'total_previous': total_previous,
            'grand_current': current,
        }

    @api.model
    def _interval_label(self, start, end):
        full_year = (start.month, start.day) == (1, 1) and (end.month, end.day) == (12, 31)
        if full_year and start.year == end.year:
            return str(start.year)
        return '%s – %s' % (start.strftime('%d/%m/%Y'), end.strftime('%d/%m/%Y'))
