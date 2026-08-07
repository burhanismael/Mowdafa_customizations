# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CpEventType(models.Model):
    """The events a child can take part in — Section 'Number of Events
    Participated' of the performance record. Master data, so the record
    ticks them as a multi-select and the report can total each."""
    _name = 'cp.event.type'
    _description = 'CP Event Type'
    _order = 'sequence, id'

    name = fields.Char(string='Event', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That event already exists.'),
    ]
