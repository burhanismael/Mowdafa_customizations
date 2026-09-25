# -*- coding: utf-8 -*-
"""One generic form printer for the whole MOWDAFA suite: the PDF mirrors
the model's FORM VIEW — same fields, same order, same section titles —
so every form model gets a faithful external-layout print without a
hand-written template per model."""
from lxml import etree

from odoo import models, api
from odoo.tools.safe_eval import safe_eval

SKIP_NAMES = {'id', 'display_name', 'name'}
SKIP_PREFIXES = ('message_', 'activity_', 'website_', 'rating_')


class MowdafaPdfHelper(models.AbstractModel):
    _name = 'mowdafa.pdf.helper'
    _description = 'Generic form PDF helper'

    def _fmt(self, record, field):
        value = record[field.name]
        if field.type == 'many2one':
            return value.display_name or ''
        if field.type == 'many2many':
            return ', '.join(value.mapped('display_name'))
        if field.type == 'selection':
            if not value:
                return ''
            return dict(
                field._description_selection(record.env)).get(value, '')
        if field.type == 'boolean':
            return '✔ Yes' if value else 'No'
        if field.type == 'date':
            return value.strftime('%d %B %Y') if value else ''
        if field.type == 'datetime':
            return value.strftime('%d %B %Y %H:%M') if value else ''
        if field.type in ('integer', 'float', 'monetary'):
            return ('%g' % value) if value else ''
        return str(value).strip() if value else ''

    def _eval_context(self, record):
        """Record values the way the web client sees them when it
        evaluates a view's invisible expressions."""
        ctx = {'context': dict(record.env.context), 'uid': record.env.uid,
               'True': True, 'False': False, 'None': None}
        for name, field in record._fields.items():
            try:
                value = record[name]
            except Exception:
                continue
            if field.type == 'many2one':
                value = value.id or False
            elif field.type in ('one2many', 'many2many'):
                value = value.ids
            elif field.type == 'binary':
                value = bool(value)
            ctx[name] = value
        return ctx

    def _hidden(self, node, attr, eval_ctx):
        """True when the node is hidden on screen for this record."""
        expr = (node.get(attr) or '').strip()
        if not expr or expr in ('0', 'False', 'false'):
            return False
        if expr in ('1', 'True', 'true'):
            return True
        try:
            return bool(safe_eval(expr, eval_ctx))
        except Exception:
            return False

    def _o2m_table(self, record, field, node, label):
        """A line table; columns follow the embedded tree view when the
        form defines one."""
        lines = record[field.name]
        tree = node.find('tree')
        columns = []
        if tree is not None:
            for cell in tree.findall('field'):
                if self._hidden(cell, 'column_invisible',
                                self._eval_context(record)):
                    continue
                if cell.get('invisible') in ('1', 'True', 'true'):
                    continue
                if cell.get('widget') == 'handle':
                    continue
                line_field = lines._fields.get(cell.get('name'))
                if line_field is None or line_field.type in (
                        'binary', 'one2many'):
                    continue
                columns.append(
                    (cell.get('string') or line_field.string, line_field))
        if not columns:
            columns = [(f.string, f) for f in lines._fields.values()
                       if f.name not in SKIP_NAMES
                       and not f.name.startswith(SKIP_PREFIXES)
                       and f.type not in ('binary', 'one2many')
                       and f.name != field.inverse_name][:8]
        return {
            'kind': 'table',
            'title': label,
            'columns': [label_ for label_, _f in columns],
            'rows': [[self._fmt(line, f) for _l, f in columns]
                     for line in lines],
        }

    def _cell(self, record, name, label):
        """One printed cell — the same shape for the generic engine and
        the fixed layouts. None for an unticked checkbox (never printed)."""
        field = record._fields[name]
        if field.type == 'binary':
            return {'label': label, 'value': '',
                    'image': record[name] or False,
                    'filled': bool(record[name]), 'signoff': True,
                    'long': False}
        if field.type == 'boolean' and not record[name]:
            return None
        text = self._fmt(record, field)
        return {'label': label, 'value': text,
                'filled': bool(record[name]),
                'note': field.type in ('text', 'html'),
                'signoff': (name.startswith(('completed_', 'officer_'))
                            or 'sign' in name),
                'long': field.type == 'text' or len(text) > 60}

    def _chunk(self, cells):
        """Two cells per printed row; long text takes a full row."""
        rows, pending = [], []
        for cell in cells:
            if cell['long']:
                if pending:
                    rows.append(pending)
                    pending = []
                rows.append([cell])
                continue
            pending.append(cell)
            if len(pending) == 2:
                rows.append(pending)
                pending = []
        if pending:
            rows.append(pending)
        return rows

    @api.model
    def grid(self, record, spec):
        """Rows for a fixed layout: spec is [(label, field_name), ...]."""
        cells = [self._cell(record, name, label) for label, name in spec]
        return self._chunk([c for c in cells if c])

    @api.model
    def layout(self, record):
        """Ordered blocks mirroring the form view: field sections (with
        the view's own titles) interleaved with line tables; drawn
        signatures collected for the footer."""
        arch = record.get_view(view_type='form')['arch']
        if isinstance(arch, str):
            arch = arch.encode()
        root = etree.fromstring(arch)

        eval_ctx = self._eval_context(record)
        blocks = []
        signs = []
        current = {'kind': 'rows', 'title': '', 'cells': []}

        def flush():
            nonlocal current
            if current['cells'] or current['title']:
                blocks.append(current)
            current = {'kind': 'rows', 'title': '', 'cells': []}

        def start_section(title):
            nonlocal current
            flush()
            current['title'] = title

        def walk(node):
            for child in node:
                if not isinstance(child.tag, str):
                    continue
                cls = child.get('class') or ''
                if 'oe_chatter' in cls or 'oe_button_box' in cls:
                    continue
                if child.tag in ('header', 'footer', 'button', 'widget'):
                    continue
                if self._hidden(child, 'invisible', eval_ctx):
                    continue
                tag = child.tag
                if tag in ('separator', 'page', 'group') \
                        and child.get('string'):
                    start_section(child.get('string'))
                if tag == 'field':
                    name = child.get('name')
                    field = record._fields.get(name)
                    if field is None or name in SKIP_NAMES \
                            or name.startswith(SKIP_PREFIXES):
                        continue
                    label = child.get('string') or field.string
                    if field.type == 'one2many':
                        flush()
                        blocks.append(
                            self._o2m_table(record, field, child, label))
                    elif field.type == 'binary' and 'sign' not in name:
                        pass            # photos etc. don't print
                    else:
                        cell = self._cell(record, name, label)
                        if cell:
                            current['cells'].append(cell)
                    continue
                walk(child)

        walk(root)
        flush()

        kept, pending_title = [], ''
        for block in blocks:
            if block['kind'] == 'rows':
                # free-text boxes (obstacles, comments, notes…) always
                # print, blank or not, so they can be read or hand-written
                # sign-off sections ("Form completed by", signatures)
                # always print too, so the form can be signed on paper
                has_data = any(c['filled'] or c.get('note')
                               or c.get('signoff')
                               for c in block['cells'])
            else:
                has_data = bool(block['rows'])
            if not has_data:
                if block['title']:
                    pending_title = block['title']
                continue
            if block['title']:
                pending_title = ''
            elif pending_title:
                block['title'] = pending_title
                pending_title = ''
            kept.append(block)
        blocks = kept

        for block in blocks:
            if block['kind'] == 'rows':
                block['rows'] = self._chunk(block['cells'])
        return {'blocks': blocks, 'signatures': signs}
