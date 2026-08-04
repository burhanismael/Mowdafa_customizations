# -*- coding: utf-8 -*-
{
    'name': 'Documents Workspace User Access',
    'version': '17.0.1.0.0',
    'category': 'Productivity/Documents',
    'summary': 'Grant read / write access to a Documents workspace to '
               'specific users, not only groups.',
    'description': """
Adds two user lists to each Documents workspace (documents.folder):

* **Read Users** — may read every document in this workspace.
* **Write Users** — may create, edit and read documents in this workspace.

These are additive to the existing group-based access: a user listed
here gets access to the workspace even if not in any of its groups.
""",
    'author': 'MOWDAFA Implementation Team',
    'license': 'LGPL-3',
    'depends': ['documents'],
    'data': [
        'security/documents_user_access_rules.xml',
        'views/documents_folder_views.xml',
    ],
    'installable': True,
    'application': False,
}
