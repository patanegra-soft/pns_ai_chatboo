# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Turn files and pictures open with the user's session, not with a token."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SESSION = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')
_ASYNC = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(encoding='utf-8')


def test_no_attachment_gets_a_token():
    for src in (_SESSION, _ASYNC):
        assert 'generate_access_token' not in src
        assert 'access_token=' not in src


def test_recovered_chips_match_old_history_by_attachment_id():
    body = _SESSION[_SESSION.index('def recover_orphan_download_chips'):]
    body = body[:body.index('\n    def ', 10)]
    assert '_ATTACHMENT_ID_IN_URL.search(' in body
    assert 'if att.id in referenced:' in body
    assert 'content_download_url(att.id, att.name, att.mimetype)' in body


def test_the_click_handler_opens_the_file_route():
    for stack, js in (('owl1', 'chatboo_component_v2.js'), ('owl2', 'chatboo_app.js')):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src' / 'js' / js
        ).read_text(encoding='utf-8')
        assert r'\/pns_ai_mcp\/session_file\/' in src
