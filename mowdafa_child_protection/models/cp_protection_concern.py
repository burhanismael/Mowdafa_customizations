# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CpProtectionConcern(models.Model):
    """Master list of primary protection concerns used on the case."""
    _name = 'cp.protection.concern'
    _description = 'CP Protection Concern'
    _order = 'sequence, id'

    name = fields.Char(string='Concern', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That concern already exists.'),
    ]
