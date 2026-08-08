# -*- coding: utf-8 -*-
from odoo import api, models


class IrRule(models.Model):
    _inherit = 'ir.rule'

    # Domains that make Documents purely user-based. A document's owner
    # keeps access to their own document; everything else flows from the
    # workspace's Read Users / Write Users lists.
    _FOLDER_DOMAIN = (
        "['|', ('read_user_ids', 'in', [user.id]), "
        "('write_user_ids', 'in', [user.id])]"
    )
    _DOC_READ_DOMAIN = (
        "['|', '|', "
        "('folder_id.read_user_ids', 'in', [user.id]), "
        "('folder_id.write_user_ids', 'in', [user.id]), "
        "('owner_id', '=', user.id)]"
    )
    # Create/edit is limited to the workspace's write users only — no
    # owner escape hatch, otherwise anyone could upload (the uploader
    # becomes the new document's owner).
    _DOC_WRITE_DOMAIN = (
        "[('folder_id.write_user_ids', 'in', [user.id])]"
    )

    @api.model
    def _apply_documents_user_based(self):
        """Force the Documents record rules onto their user-based form.
        Called from data on every module update, so it applies even
        though the original rules live in noupdate blocks."""
        mapping = {
            'documents.documents_folder_groups_rule': self._FOLDER_DOMAIN,
            'documents.documents_document_readonly_rule': self._DOC_READ_DOMAIN,
            'documents.documents_document_write_rule': self._DOC_WRITE_DOMAIN,
        }
        for xmlid, domain in mapping.items():
            rule = self.env.ref(xmlid, raise_if_not_found=False)
            if rule:
                rule.sudo().write({'domain_force': domain})
