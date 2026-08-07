# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
