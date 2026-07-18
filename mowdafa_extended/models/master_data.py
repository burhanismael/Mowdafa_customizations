# -*- coding: utf-8 -*-
from odoo import models, fields


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
