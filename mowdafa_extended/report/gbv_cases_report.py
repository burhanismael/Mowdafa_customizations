# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ReportGbvCases(models.AbstractModel):
    _name = 'report.mowdafa_extended.report_gbv_cases_document'
    _description = 'GBV Cases Statistical Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        wizard = self.env['gbv.case.report.wizard'].browse(
            data.get('wizard_id') or docids or [])
        if not wizard.exists():
            raise UserError(_(
                'This report window has expired. Open the wizard from '
                'GBV > Reporting and print again.'))
        wizard.ensure_one()
        return {
            'doc_ids': wizard.ids,
            'doc_model': 'gbv.case.report.wizard',
            'docs': wizard,
            'wizard': wizard,
            'blocks': wizard._build_blocks(),
            'company': wizard.company_id,
        }
