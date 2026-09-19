# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class GbvIntake(models.Model):
    """The client intake form: who the survivor is, why the service is
    sought, and the signed consent to keep it on file."""
    _name = 'gbv.intake'
    _description = 'GBV Client Intake Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference', readonly=True, copy=False, default='New')
    case_id = fields.Many2one(
        'gbv.case', string='Case', required=True, ondelete='cascade')

    # ── personal information ─────────────────────────────────────────────
    client_name = fields.Char(string='Name')
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female')], string='Gender')
    email = fields.Char(string='E-Mail')
    phone = fields.Char(string='Phone')
    date_of_birth = fields.Date(string='Date of Birth')

    # ── location (from the case) ─────────────────────────────────────────
    country_id = fields.Many2one(
        'res.country', string='Country',
        default=lambda self: self.env.ref('base.so', raise_if_not_found=False))
    region_id = fields.Many2one('gbv.region', string='Region')
    district_id = fields.Many2one(
        'gbv.district', string='District',
        domain="[('region_id', '=?', region_id)]")

    # ── service request ──────────────────────────────────────────────────
    service_reason = fields.Text(
        string='What is the reason for seeking our services?')
    heard_about = fields.Char(string='How did you hear about us?')

    # ── signature ────────────────────────────────────────────────────────
    sign = fields.Char(string='Signature')
    sign_img = fields.Binary(string='Signature (drawn)')
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'gbv.intake') or 'New'
        return super().create(vals_list)

    def action_view_case(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Case'),
            'res_model': 'gbv.case',
            'view_mode': 'form',
            'res_id': self.case_id.id,
        }
