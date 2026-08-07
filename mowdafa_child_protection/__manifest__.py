# -*- coding: utf-8 -*-
{
    'name': 'Mowdafa Child Protection',
    'version': '17.0.1.0.0',
    'category': 'Services',
    'summary': 'Child protection case management: managed children and '
               'partner-deposited records (cp.case), with dashboard',
    'description': """
MOWDAFA — Child Protection Case Management
==========================================
One model, ``cp.case``, split by ``record_type``:

* **managed** — children MOWDAFA cares for directly (CP/YYYY/NNNN,
  six live stages, verification recommendation, photo restricted).
* **partner** — records partner agencies deposit: the 12-section
  Puntland CP form keyed verbatim, read-only, out of the pipeline
  but counted in the statistics (CP-16/17).

This first phase ships the case form, the menus and the supervisor
dashboard. The nine managed-track satellite forms follow.
""",
    'author': 'MOWDAFA Implementation Team',
    'license': 'LGPL-3',
    'depends': ['mowdafa_extended'],
    'data': [
        # security
        'security/cp_groups.xml',
        'security/ir.model.access.csv',
        # spine (defines the root menu)
        'views/cp_case_views.xml',
        'views/cp_partner_record_views.xml',
        'views/cp_child_views.xml',
        # master tables (define the actions the menus point at)
        'views/cp_partner_agency_views.xml',
        'views/cp_basic_need_views.xml',
        'views/cp_event_type_views.xml',
        'views/cp_performance_rating_views.xml',
        'views/cp_case_worker_views.xml',
        'views/cp_supervisor_views.xml',
        'views/cp_protection_concern_views.xml',
        # managed-track forms
        'views/cp_placement_views.xml',
        'views/cp_handover_views.xml',
        'views/cp_registration_views.xml',
        'views/cp_verification_views.xml',
        'views/cp_daily_record_views.xml',
        'views/cp_mentoring_views.xml',
        'views/cp_psychosocial_views.xml',
        'views/cp_reunification_views.xml',
        'views/cp_followup_views.xml',
        # menus last — they reference the actions above
        'views/cp_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mowdafa_child_protection/static/src/cp_dashboard/**/*',
            'mowdafa_child_protection/static/src/cp_forms.css',
        ],
    },
    'installable': True,
    'application': True,
}
