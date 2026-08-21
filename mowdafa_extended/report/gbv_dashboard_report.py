# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ReportGbvDashboard(models.AbstractModel):
    _name = 'report.mowdafa_extended.report_gbv_dashboard_document'
    _description = 'GBV Dashboard Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        wizard = self.env['gbv.dashboard.report.wizard'].browse(
            data.get('wizard_id') or docids or [])
        if not wizard.exists():
            raise UserError(_(
                'This report window has expired. Open the wizard from '
                'GBV > Reporting and print again.'))
        wizard.ensure_one()
        return {
            'doc_ids': wizard.ids,
            'doc_model': 'gbv.dashboard.report.wizard',
            'docs': wizard,
            'wizard': wizard,
            'report': wizard._build_report_data(),
            'company': wizard.company_id,
        }
