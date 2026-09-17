# -*- coding: utf-8 -*-
from odoo import models, fields


class CpReferralSource(models.Model):
    """Master list of referral sources picked on the ministry case."""
    _name = 'cp.referral.source'
    _description = 'CP Referral Source'
    _order = 'sequence, id'

    name = fields.Char(string='Referral Source', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That referral source already exists.'),
    ]
