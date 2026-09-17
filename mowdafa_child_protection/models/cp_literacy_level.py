# -*- coding: utf-8 -*-
from odoo import models, fields


class CpLiteracyLevel(models.Model):
    """Master list of literacy levels picked on the registration form."""
    _name = 'cp.literacy.level'
    _description = 'CP Literacy Level'
    _order = 'sequence, id'

    name = fields.Char(string='Literacy Level', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That literacy level already exists.'),
    ]
