# -*- coding: utf-8 -*-
from odoo import models, fields


class CpReferrerType(models.Model):
    """Master list of referring persons / organizations picked on the
    registration form."""
    _name = 'cp.referrer.type'
    _description = 'CP Referrer Type'
    _order = 'sequence, id'

    name = fields.Char(string='Referrer', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That referrer already exists.'),
    ]
