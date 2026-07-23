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
        'security/ir.model.access.csv',
        'views/cp_case_views.xml',
        'views/cp_partner_record_views.xml',
        'views/cp_forms_views.xml',
        'views/cp_master_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mowdafa_child_protection/static/src/cp_dashboard/**/*',
        ],
    },
    'installable': True,
    'application': True,
}
