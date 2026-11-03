# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""PNS-65: the browser-chosen file kind sets the stored MIME type.

The client used to declare the mimetype of what it uploaded, so any file
could be stored under a type it is not. The server now picks the type from
the declared kind and ignores whatever the client sent. Word exports also
escape the image address like every other attribute value.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SESSION = (
    _ROOT / 'common' / 'models' / 'chatboo_session.py'
).read_text(encoding='utf-8')


def test_kind_decides_mimetype():
    assert "'doc': 'application/msword'" in _SESSION
    assert "'html': 'text/html'" in _SESSION
    assert "'pdf': 'application/pdf'" in _SESSION
    assert "_CLIENT_EXPORT_MIMETYPES.get(kind)" in _SESSION


def test_client_mimetype_is_not_trusted():
    assert "mimetype = self._CLIENT_EXPORT_MIMETYPES.get(kind)" in _SESSION


def test_pending_document_is_built_only_on_click():
    """Painting a turn must not upload; the chip click does."""
    for stack, app in (
        ('owl1', 'chatboo_component_v2.js'),
        ('owl2', 'chatboo_app.js'),
    ):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src'
            / 'js' / app
        ).read_text(encoding='utf-8')
        assert '_fulfillChipClick' in src
        assert '_fulfillPendingExportsInView' not in src
        assert 'fulfillPendingSessionDocuments(msg, sourceEl, this._exportCtx(), chip)' in src
        export = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src'
            / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        assert 'function fulfillPendingSessionDocuments(msg, sourceEl, ctx, onlyChip)' in export


def test_export_escapes_image_address():
    for stack in ('owl1', 'owl2'):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src'
            / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        assert 'function escapeWordAttr' in src
        assert 'escapeWordAttr(img)' in src
        assert 'escapeWordAttr(c.dataUrl)' in src
