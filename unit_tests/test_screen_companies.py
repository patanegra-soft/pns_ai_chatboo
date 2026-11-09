# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""On the web, Chatboo works in the companies the switcher ticks."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_MODELS = _ROOT / 'common' / 'models'
_REQUEST = (_MODELS / 'chatboo_async_request.py').read_text(encoding='utf-8')
_SESSION = (_MODELS / 'chatboo_session.py').read_text(encoding='utf-8')
_CONTROLLERS = [
    (_ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py')
    .read_text(encoding='utf-8')
    for stack in ('owl1', 'owl2', 'owl3')
]


def _method(source, name, sep='\n    def '):
    return source.split('def %s' % name, 1)[1].split(sep, 1)[0]


def test_every_stack_sends_the_switcher_with_the_question():
    for source in _CONTROLLERS:
        cookie = _method(source, '_screen_company_ids')
        assert "cookies.get('cids')" in cookie
        assert "raw.replace('-', ',').split(',')" in cookie
        assert 'screen_ids(' in cookie
        assert 'screen_company_ids=self._screen_company_ids(),' in source


def test_the_header_does_not_repeat_the_switcher():
    """Odoo's switcher already shows the companies; a second label looked selectable."""
    for source in _CONTROLLERS:
        assert '_ai_company' not in source
        assert "'ai_company'" not in source
    for stack in ('owl1', 'owl2', 'owl3'):
        static = _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src'
        for path in list(static.rglob('*.js')) + list(static.rglob('*.xml')):
            text = path.read_text(encoding='utf-8')
            assert 'aiCompany' not in text, path
            assert 'o_chatboo_company' not in text, path


def test_the_job_keeps_the_switcher_and_hands_it_to_the_engine():
    assert "screen_company_ids = fields.Char(" in _REQUEST
    enqueue = _method(_REQUEST, '_enqueue')
    assert "'screen_company_ids': (" in enqueue
    process = _method(_REQUEST, '_process')
    assert '**{SCREEN_COMPANIES: self._screen_companies()},' in process


def test_rows_from_other_companies_are_not_reused():
    process = _method(_REQUEST, '_process')
    assert 'get_fresh_query_data(\n                self._turn_company_ids())' in process
    save = _method(_REQUEST, '_save_to_session')
    assert "'last_query_company_ids': json.dumps(self._turn_company_ids())," in save
    fresh = _method(_SESSION, 'get_fresh_query_data')
    assert 'sorted(cached) != sorted(company_ids)' in fresh
