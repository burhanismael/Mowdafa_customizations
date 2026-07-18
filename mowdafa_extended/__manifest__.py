# -*- coding: utf-8 -*-
{
    'name': 'Mowdafa Extended',
    'version': '17.0.1.0.0',
    'category': 'Services',
    'summary': 'Survivor case form with case worker, guardian and signatures',
    'description': """
Survivor Case Form
==================
Records survivor cases with case worker, guardian details and
signatures of the guardian, case worker and survivor.
    """,
    'author': 'Yugal Vyas',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'report/consent_for_services_report.xml',
        'report/gbv_cases_paperformat.xml',
        'report/gbv_cases_report_templates.xml',
        'report/gbv_cases_report_actions.xml',
        'views/survivor_case_views.xml',
        'views/survivor_master_views.xml',
        'views/case_worker_views.xml',
        'views/admission_form_views.xml',
        'views/action_plan_views.xml',
        'views/followup_form_views.xml',
        'views/referral_form_views.xml',
        'views/case_closure_views.xml',
        'views/master_data_views.xml',
        'views/gbv_case_views.xml',
        'wizard/gbv_case_report_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mowdafa_extended/static/src/justice_stage/**/*',
            'mowdafa_extended/static/src/gbv_dashboard/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
