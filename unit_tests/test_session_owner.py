# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Own session on the HTTP door, and HTML cleaned before it is painted."""
from pathlib import Path
from _deployed import deployed

_ROOT = Path(__file__).resolve().parents[1]


def test_controllers_keep_a_session_on_its_owner():
    for stack in ('owl1', 'owl2'):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'controllers' / 'chatboo.py'
        ).read_text(encoding='utf-8')
        # Reading the owner of someone else's row trips the record rule: search it.
        assert '.user_id.id != request.env' not in src
        assert "('user_id', '=', request.env.uid)" in src


def test_formatter_sanitizes_html_before_innerhtml():
    for stack in ('owl1', 'owl2'):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / 'chatboo_formatters.js'
        ).read_text(encoding='utf-8')
        assert 'function sanitizeHtml' in src
        assert '_ALLOWED_TAGS' in src
        assert '_UNSAFE_TAGS' not in src


def test_owl1_extends_the_user_field_lists():
    src = (
        deployed('owl1', 'models', 'res_users.py')
    ).read_text(encoding='utf-8')
    assert 'def __init__(self, pool, cr)' in src
    assert 'SELF_READABLE_FIELDS = readable' in src
    assert '@property' not in src
    owl2 = (
        deployed('owl2', 'models', 'res_users.py')
    ).read_text(encoding='utf-8')
    assert '@property' in owl2
    assert 'def SELF_READABLE_FIELDS' in owl2
