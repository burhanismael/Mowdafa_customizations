# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SurvivorMaster(models.Model):
    _name = 'survivor.master'
    _description = 'Survivor Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'generated_code'
    _rec_names_search = ['generated_code', 'survivor_name']
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

    def init(self):
        self.env.cr.execute(
            "UPDATE survivor_master SET generated_code = UPPER(generated_code) "
            "WHERE generated_code IS NOT NULL AND generated_code != UPPER(generated_code)"
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
                value = (value or '').strip().upper()
                code += value[2] if len(value) >= 3 else ''
            record.generated_code = code
