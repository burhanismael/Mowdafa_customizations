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
    'author': 'Odoo Developer',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/survivor_case_views.xml',
        'views/survivor_master_views.xml',
        'views/case_worker_views.xml',
        'views/admission_form_views.xml',
        'report/consent_for_services_report.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
