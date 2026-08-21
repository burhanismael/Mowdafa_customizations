# -*- coding: utf-8 -*-
from odoo import models, fields, api

# The Puntland regions and their districts/localities exactly as the
# printed report lists them, in print order. Seeded on install/upgrade so
# every region prints its card even before anyone opens Configuration.
# 'degmo' prints "Degmada X", 'deegaan' prints "Deegaanka X".
REFERENCE_DISTRICTS = [
    ('Karkaar', [
        ('Qardho', 'degmo'),
        ('Waaciye', 'degmo'),
        ('Shire', 'deegaan'),
        ('Gerihel', 'deegaan'),
        ('Sanjilbo', 'deegaan'),
        ('Kurduxo', 'deegaan'),
        ('Adisoone', 'deegaan'),
        ('Qalwo', 'deegaan'),
    ]),
    ('Nugaal', [
        ('Garowe', 'degmo'),
        ('Eyl', 'degmo'),
        ('Buurtinle', 'degmo'),
        ('Dangorayo', 'degmo'),
        ('G. Jiiraan', 'degmo'),
    ]),
    ('Bari', [
        ('Bosaso', 'degmo'),
        ('Carmo', 'degmo'),
        ('Iskushuban', 'degmo'),
        ('Ufeyn', 'degmo'),
        ('Dhaadaar', 'deegaan'),
    ]),
    ('Raascasayr', [
        ('Geeselay', 'degmo'),
        ('Xaabo', 'degmo'),
    ]),
    ('Mudug', [
        ('Galkacyo', 'degmo'),
        ('Garacad', 'degmo'),
        ('Xarfo', 'degmo'),
        ('Jariiban', 'degmo'),
    ]),
    ('Sanaag', [
        ('Badhan', 'degmo'),
        ('Xingalool', 'degmo'),
        ('Hadaaftimo', 'degmo'),
    ]),
    ('Haylaan', [
        ('Dhahar', 'degmo'),
    ]),
]


class GbvRegion(models.Model):
    _name = 'gbv.region'
    _description = 'Region'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    somali_name = fields.Char(string='Somali Name')
    sequence = fields.Integer(string='Sequence', default=10)


class GbvDistrict(models.Model):
    _name = 'gbv.district'
    _description = 'GBV District / Locality (Degmo / Deegaan)'
    _order = 'region_id, sequence, id'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    somali_name = fields.Char(string='Somali Name')
    region_id = fields.Many2one(
        comodel_name='gbv.region',
        string='Region (Gobol)',
        ondelete='cascade',
        index=True,
        help='Used to filter districts by the case region.',
    )
    level = fields.Selection([
        ('degmo', 'District (Degmada)'),
        ('deegaan', 'Locality (Deegaanka)'),
    ], string='Level', default='degmo', required=True,
        help='Only affects the Somali prefix printed on the report: '
             'Degmada X or Deegaanka X.')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_region_uniq', 'unique(name, region_id)',
         'That district already exists in this region.'),
    ]

    @property
    def somali_label(self):
        self.ensure_one()
        prefix = 'Deegaanka' if self.level == 'deegaan' else 'Degmada'
        return '%s %s' % (prefix, self.somali_name or self.name)

    def init(self):
        self._seed_reference_districts()

    @api.model
    def _seed_reference_districts(self):
        """Bring the region/district master data in line with the printed
        report. Existing rows are matched on a punctuation-insensitive
        name so anything typed in by hand is reused rather than
        duplicated, and only genuine differences are written."""
        def key(*values):
            return next((''.join(c for c in value.lower() if c.isalnum())
                         for value in values if value), '')

        Region = self.env['gbv.region']
        District = self.with_context(active_test=False)
        regions = {}
        for region in Region.search([]):
            regions.setdefault(key(region.name), region)
            regions.setdefault(key(region.somali_name), region)
        regions.pop('', None)

        for region_name, districts in REFERENCE_DISTRICTS:
            region = regions.get(key(region_name))
            if not region:
                region = Region.create({'name': region_name})
                regions[key(region_name)] = region
            existing = {}
            for district in District.search([('region_id', '=', region.id)]):
                existing.setdefault(key(district.name), district)
                existing.setdefault(key(district.somali_name), district)
            existing.pop('', None)
            for index, (name, level) in enumerate(districts, start=1):
                values = {'sequence': index * 10, 'level': level}
                district = existing.get(key(name))
                if not district:
                    District.create(dict(values, name=name,
                                         region_id=region.id))
                elif any(district[field] != value
                         for field, value in values.items()):
                    district.write(values)

    def _compute_display_name(self):
        for record in self:
            record.display_name = '%s / %s' % (
                record.region_id.name or '', record.name or '')


class GbvViolenceType(models.Model):
    _name = 'gbv.violence.type'
    _description = 'Violence Type'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    somali_name = fields.Char(
        string='Somali Name',
        help='Used in the statistical report title, e.g. KUFSIGA.')


class GbvRiskLevel(models.Model):
    _name = 'gbv.risk.level'
    _description = 'Risk Level'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')


# Seeded on install/upgrade so the perpetrator lines keep their old
# selection labels; the old selection key is kept to migrate stored rows.
PERPETRATOR_RELATIONSHIPS = [
    ('family', 'Family member'),
    ('partner', 'Intimate partner'),
    ('neighbour', 'Neighbour / Community'),
    ('authority', 'Person in authority'),
    ('stranger', 'Stranger'),
    ('unknown', 'Unknown'),
]


class GbvPerpetratorRelationship(models.Model):
    _name = 'gbv.perpetrator.relationship'
    _description = 'Perpetrator Relationship to Survivor'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'That relationship already exists.'),
    ]

    def init(self):
        self._seed_relationships()

    @api.model
    def _seed_relationships(self):
        Relationship = self.with_context(active_test=False)
        existing = {
            (record.name or '').strip().lower()
            for record in Relationship.search([])}
        for index, (_key, label) in enumerate(PERPETRATOR_RELATIONSHIPS,
                                              start=1):
            if label.strip().lower() not in existing:
                Relationship.create({'name': label, 'sequence': index * 10})

    @api.model
    def _default_unknown(self):
        return self.search([('name', '=ilike', 'unknown')], limit=1)
