# -*- coding: utf-8 -*-
from odoo import fields, models


class DocumentsFolder(models.Model):
    _inherit = 'documents.folder'

    read_user_ids = fields.Many2many(
        'res.users', 'documents_folder_read_user_rel',
        'folder_id', 'user_id', string='Read Users',
        help='These users may read every document in this workspace, '
             'in addition to the read groups.')
    write_user_ids = fields.Many2many(
        'res.users', 'documents_folder_write_user_rel',
        'folder_id', 'user_id', string='Write Users',
        help='These users may create, edit and read documents in this '
             'workspace, in addition to the write groups.')

    def _compute_has_write_access(self):
        """Upload rights follow the Write Users list: only a workspace's
        write users (and Documents Managers) may upload."""
        super()._compute_has_write_access()
        if self.env.su or self.user_has_groups(
                'documents.group_documents_manager'):
            return
        uid = self.env.user.id
        for record in self:
            record.has_write_access = uid in record.write_user_ids.ids
