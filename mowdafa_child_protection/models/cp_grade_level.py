# -*- coding: utf-8 -*-
from odoo import models, fields


class CpGradeLevel(models.Model):
    """Master list of grade levels picked as 'Highest grade completed'
    on the registration form."""
    _name = 'cp.grade.level'
    _description = 'CP Grade Level'
    _order = 'sequence, id'

    name = fields.Char(string='Grade Level', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That grade level already exists.'),
    ]
