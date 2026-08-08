# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    def _cp_check_folder_write(self, folder):
        """Raise a clear message when a read-only user tries to create,
        edit or delete a document in a workspace they cannot write to.
        Managers, the superuser and system calls are never blocked."""
        user = self.env.user
        if self.env.su or user._is_system() or user.has_group(
                'documents.group_documents_manager'):
            return
        if folder and not folder.has_write_access:
            raise UserError(_(
                "You have read-only access to the \"%s\" workspace, so you "
                "cannot create, edit or delete documents in it. Please ask "
                "a workspace Write User or a Documents Manager.",
                folder.display_name))

    @api.model_create_multi
    def create(self, vals_list):
        Folder = self.env['documents.folder']
        for vals in vals_list:
            folder = Folder.browse(vals.get('folder_id')) \
                if vals.get('folder_id') else Folder
            self._cp_check_folder_write(folder)
        return super().create(vals_list)

    def write(self, vals):
        # editing where the document currently lives …
        for document in self:
            self._cp_check_folder_write(document.folder_id)
        # … and moving it into a new workspace
        if vals.get('folder_id'):
            self._cp_check_folder_write(
                self.env['documents.folder'].browse(vals['folder_id']))
        return super().write(vals)

    def unlink(self):
        for document in self:
            self._cp_check_folder_write(document.folder_id)
        return super().unlink()
