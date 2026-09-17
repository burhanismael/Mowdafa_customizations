# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    """Flags saying which programme directories an employee may appear
    in: the GBV case-worker master, the Child Protection ones, or both."""
    _inherit = 'hr.employee'

    is_gbv_worker = fields.Boolean(
        string='GBV',
        help='Show this employee in the GBV case worker directory.')
    is_cp_worker = fields.Boolean(
        string='Child Protection',
        help='Show this employee in the Child Protection case worker '
             'and supervisor directories.')
