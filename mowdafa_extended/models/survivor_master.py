# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SurvivorMaster(models.Model):
    _name = 'survivor.master'
    _description = 'Survivor Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'survivor_name'
    _order = 'id desc'

    survivor_name = fields.Char(
        string='Survivor Name',
        required=True,
        tracking=True,
    )
    mother_first_name = fields.Char(
        string="Mother's First Name",
        required=True,
        tracking=True,
    )
    birth_date = fields.Date(
        string='Birth Date',
        required=True,
        tracking=True,
    )
    birth_order = fields.Char(
        string='Birth Order (Digits)',
        required=True,
        tracking=True,
    )
    place_of_birth = fields.Char(
        string='Place of Birth',
        required=True,
        tracking=True,
    )
    generated_code = fields.Char(
        string='Generated Code',
        compute='_compute_generated_code',
        store=True,
        tracking=True,
    )

    @api.depends('mother_first_name', 'birth_date',
                 'birth_order', 'place_of_birth')
    def _compute_generated_code(self):
        for record in self:
            birth_year = ''
            birth_month = ''
            if record.birth_date:
                birth_year = record.birth_date.strftime('%Y')
                birth_month = record.birth_date.strftime('%B')
            parts = [
                record.mother_first_name,
                birth_year,
                birth_month,
                record.birth_order,
                record.place_of_birth,
            ]
            code = ''
            for value in parts:
                value = (value or '').strip().lower()
                code += value[2] if len(value) >= 3 else ''
            record.generated_code = code
