# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CpBasicNeed(models.Model):
    """Section 6 of the partner form lists basic needs as a multi-select
    (Food, Education, Psychosocial Support, Health Care, Legal Support,
    Other), so they are master data rather than free text — the partner
    report can then total them."""
    _name = 'cp.basic.need'
    _description = 'CP Basic Need'
    _order = 'sequence, id'

    name = fields.Char(string='Basic Need', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That basic need already exists.'),
    ]
