# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CpPartnerAgency(models.Model):
    """The partner-record master: the agencies whose children MOWDAFA
    holds records for (UNICEF, Save the Children, GREDO, NRC, local
    CBOs…). Its own table, so the partner report's agency breakdown
    never depends on the general contacts directory."""
    _name = 'cp.partner.agency'
    _description = 'CP Partner Agency'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Agency', required=True, tracking=True)
    short_name = fields.Char(
        string='Short Name',
        help='Used in the deposited-records register, where the full '
             'agency name would not fit — e.g. "UNICEF" for "UNICEF — '
             'Child Protection sub-cluster".')
    code = fields.Char(string='Code')
    sector = fields.Char(
        string='Sector', help='e.g. Child Protection sub-cluster')
    focal_point_id = fields.Many2one(
        'case.worker', string='Caseworker', tracking=True,
        help='The agency\'s usual caseworker. Filled onto a new partner '
             'record automatically, and learned back from the first '
             'record that names one.')
    supervisor_id = fields.Many2one(
        'case.worker', string='Supervisor', tracking=True,
        help='Filled onto a new partner record automatically, and '
             'learned back from the first record that names one.')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'That agency already exists.'),
    ]


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
