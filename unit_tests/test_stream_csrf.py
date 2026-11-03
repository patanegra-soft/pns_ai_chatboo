# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Another site cannot start a turn: /chatboo/stream checks Odoo's CSRF token."""
from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_JS = {'owl1': 'chatboo_component_v2.js', 'owl2': 'chatboo_app.js'}


@pytest.mark.parametrize('stack', ['owl1', 'owl2'])
def test_the_route_keeps_csrf_and_no_open_cors(stack):
    src = (
        _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py'
    ).read_text(encoding='utf-8')
    line = next(l for l in src.splitlines() if "'/chatboo/stream'" in l and '@http.route' in l)
    assert 'csrf=False' not in line
    assert 'cors=' not in line


@pytest.mark.parametrize('stack', ['owl1', 'owl2'])
def test_the_client_sends_the_token(stack):
    src = (
        _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src' / 'js' / _JS[stack]
    ).read_text(encoding='utf-8')
    assert 'fetch(ChatbooTurn.streamUrl(odoo.csrf_token), {' in src
    core = (_ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_turn.js').read_text(encoding='utf-8')
    assert '"?csrf_token=" + encodeURIComponent(csrfToken' in core
    assert "fetch('/chatboo/stream'" not in src
    assert 'fetch("/chatboo/stream"' not in src


@pytest.mark.parametrize('stack', ['owl1', 'owl2'])
def test_a_stale_token_says_reload_instead_of_http_400(stack):
    base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
    src = (base / 'static' / 'src' / 'js' / _JS[stack]).read_text(encoding='utf-8')
    assert 'throw new Error(await this._streamRefusal(resp));' in src
    refusal = src.split('async _streamRefusal(resp) {', 1)[1].split('\n    }\n', 1)[0]
    assert 'ChatbooTurn.refusal(resp, _t(' in refusal
    assert 'Reload the page (F5).' in refusal
    assert 'CSRF' not in refusal
    if stack == 'owl1':
        assert 'Communication Error: ${error.message' not in src
        assert src.count('Communication Error: ${this._escapeHtml(error.message') == 2
    po = 'es.po' if stack == 'owl1' else 'es_ES.po'
    catalog = (base / 'i18n' / po).read_text(encoding='utf-8')
    entry = catalog.split('msgid "Your session has changed. Reload the page (F5)."', 1)
    assert 'code:addons/pns_ai_chatboo/static/src/js/%s:0' % _JS[stack] in entry[0].rsplit('#. module', 1)[1]
    assert entry[1].startswith('\nmsgstr "Tu sesión ha cambiado. Recarga la página (F5)."')
